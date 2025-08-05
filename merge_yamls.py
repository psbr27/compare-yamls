import argparse
import json
import os
import subprocess

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import LiteralScalarString


class YamlMerger:
    def __init__(self, base_yaml, next_version_yaml, validate_helm=False):
        self.base_yaml = base_yaml
        self.next_version_yaml = next_version_yaml
        self.validate_helm = validate_helm
        self.next_version_duplicate = self.next_version_yaml.replace(
            ".yml", "_duplicate.yml"
        )
        self.yaml = YAML()
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        self.merge_output_path = self._get_merge_output_path()
        self.changes = []

    def _get_merge_output_path(self):
        base_filename = os.path.basename(self.next_version_yaml)
        if base_filename.endswith(".yml"):
            merge_filename = base_filename[:-4] + "_merge.yaml"
        elif base_filename.endswith(".yaml"):
            merge_filename = base_filename[:-5] + "_merge.yaml"
        else:
            merge_filename = base_filename + "_merge.yaml"
        return os.path.join(self.output_dir, merge_filename)

    def duplicate_next_version(self):
        if os.path.abspath(self.next_version_yaml) != os.path.abspath(
            self.next_version_duplicate
        ):
            with open(self.next_version_yaml, "r") as src, open(
                self.next_version_duplicate, "w"
            ) as dst:
                data = self.yaml.load(src)
                self.yaml.dump(data, dst)
            print(f"Created duplicate: {self.next_version_duplicate}")
        else:
            print("Source and duplicate file names are the same. Skipping copy.")

    def load_yamls(self):
        with open(self.base_yaml, "r") as f:
            self.base_data = self.yaml.load(f)
        with open(self.next_version_duplicate, "r") as f:
            self.next_version_data = self.yaml.load(f)

    def quote_strings_inplace(self, obj):
        if isinstance(obj, CommentedMap):
            for k, v in obj.items():
                obj[k] = self.quote_strings_inplace(v)
            return obj
        if isinstance(obj, CommentedSeq):
            for idx, v in enumerate(obj):
                obj[idx] = self.quote_strings_inplace(v)
            return obj
        if isinstance(obj, str):
            if "\n" in obj:
                return LiteralScalarString(obj)
            return obj
        return obj

    def merge_yaml(self, base, target, path=None, changes=None):
        if path is None:
            path = []
        if changes is None:
            changes = []
        resource_keys = {
            "resources",
            "limits",
            "requests",
            "cpu",
            "memory",
            "ephemeral-storage",
        }
        for key in base:
            if key in ("tag", "envNFVersion"):
                continue
            if key in resource_keys:
                continue
            if key == "extraContainersTpl":
                continue
            current_path = path + [str(key)]
            if key not in target:
                target[key] = base[key]
                changes.append(
                    {
                        "path": ".".join(current_path),
                        "type": "added",
                        "new": base[key],
                    }
                )
            else:
                if isinstance(base[key], dict) and isinstance(target[key], dict):
                    self.merge_yaml(base[key], target[key], current_path, changes)
                elif base[key] != target[key]:
                    old_value = target[key]
                    target[key] = base[key]
                    changes.append(
                        {
                            "path": ".".join(current_path),
                            "type": "updated",
                            "old": old_value,
                            "new": base[key],
                        }
                    )
        return changes

    def write_merged_yaml(self):
        self.quote_strings_inplace(self.next_version_data)
        with open(self.merge_output_path, "w") as f:
            self.yaml.dump(self.next_version_data, f)
        print(f"Merged YAML written to: {self.merge_output_path}")

    def validate_yaml(self):
        try:
            with open(self.merge_output_path, "r") as f:
                _ = self.yaml.load(f)
            print(f"Validation: {self.merge_output_path} is a valid YAML file.")
        except Exception as e:
            print(
                f"Validation Error: {self.merge_output_path} is NOT a valid YAML file! Error: {e}"
            )

    def kubectl_validate(self):
        try:
            result = subprocess.run(
                [
                    "kubectl",
                    "apply",
                    "--dry-run=client",
                    "-f",
                    self.merge_output_path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            print(f"Kubernetes schema validation passed for {self.merge_output_path}.")
        except subprocess.CalledProcessError as e:
            print(f"Kubernetes schema validation failed for {self.merge_output_path}:")
            print(e.stdout)
            print(e.stderr)

    def helm_validate(self):
        config_path = "config.json"
        chart_path = None
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    chart_path = config.get("chart_path")
            except Exception as e:
                print(f"Could not read config.json: {e}")
        if chart_path:
            print(
                f"Running Helm template and Kubernetes validation using chart at: {chart_path}"
            )
            try:
                helm_cmd = [
                    "helm",
                    "template",
                    chart_path,
                    "--values",
                    self.merge_output_path,
                ]
                helm_proc = subprocess.Popen(
                    helm_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                kubectl_cmd = [
                    "kubectl",
                    "apply",
                    "--dry-run=client",
                    "-f",
                    "-",
                ]
                kubectl_proc = subprocess.Popen(
                    kubectl_cmd,
                    stdin=helm_proc.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                helm_proc.stdout.close()
                out, err = kubectl_proc.communicate()
                if kubectl_proc.returncode == 0:
                    print("Helm/Kubernetes manifest validation passed.")
                else:
                    print("Helm/Kubernetes manifest validation failed:")
                    print(out.decode())
                    print(err.decode())
            except Exception as e:
                print(f"Error running Helm/Kubernetes validation: {e}")
        else:
            print(
                "Helm validation enabled, but chart_path not found in config.json. Skipping Helm validation."
            )

    def write_diff_report(self):
        def format_value(val):
            import json as _json

            if isinstance(val, (dict, list)):
                return _json.dumps(val, ensure_ascii=False)
            return str(val)

        diff_output_path = os.path.join(self.output_dir, "diff.txt")
        with open(diff_output_path, "w") as f:
            for change in self.changes:
                if change["type"] == "updated":
                    f.write(
                        f"{change['path']}: updated | old: {format_value(change['old'])} | new: {format_value(change['new'])}\n"
                    )
                elif change["type"] == "added":
                    f.write(
                        f"{change['path']}: added | new: {format_value(change['new'])}\n"
                    )
        print(f"Diff report written to: {diff_output_path}")

    def run(self):
        self.duplicate_next_version()
        self.load_yamls()
        self.changes = self.merge_yaml(self.base_data, self.next_version_data)
        self.write_merged_yaml()
        self.validate_yaml()
        self.kubectl_validate()
        if self.validate_helm:
            self.helm_validate()
        else:
            print("Helm validation not enabled. Skipping Helm validation.")
        self.write_diff_report()


def main():
    parser = argparse.ArgumentParser(
        description="Merge YAMLs with optional Helm validation."
    )
    parser.add_argument("base_yaml", help="Base YAML file")
    parser.add_argument("next_version_yaml", help="Next version YAML file")
    parser.add_argument(
        "--validate-helm",
        action="store_true",
        help="Enable Helm/Kubernetes manifest validation (requires chart path in config.json)",
    )
    args = parser.parse_args()
    merger = YamlMerger(
        base_yaml=args.base_yaml,
        next_version_yaml=args.next_version_yaml,
        validate_helm=args.validate_helm,
    )
    merger.run()


if __name__ == "__main__":
    main()
