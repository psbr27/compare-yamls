"""YAML merging operations with configurable strategies."""

import copy
from typing import Any, Dict, List, Optional

import yaml

from exceptions import YamlSyntaxError


class YamlMerger:
    """Handles YAML file merging with configurable strategies."""

    def __init__(
        self, list_merge_strategy: str = "replace", deletion_strategy: str = "ignore"
    ) -> None:
        """Initialize YAML merger with strategies.

        Args:
            list_merge_strategy: Strategy for merging lists ('replace', 'append', 'intelligent')
            deletion_strategy: Strategy for handling deletions ('ignore', 'remove')
        """
        self.list_merge_strategy = list_merge_strategy
        self.deletion_strategy = deletion_strategy
        self._changes: List[Dict[str, Any]] = []

    def load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """Load and parse a YAML file.

        Args:
            file_path: Path to the YAML file

        Returns:
            Parsed YAML content as dictionary

        Raises:
            YamlSyntaxError: If YAML file contains syntax errors
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = yaml.safe_load(file)
                return content if content is not None else {}
        except yaml.YAMLError as e:
            raise YamlSyntaxError(str(e), file_path) from e
        except IOError as e:
            raise YamlSyntaxError(f"Cannot read file: {e}", file_path) from e

    def save_yaml_file(self, data: Dict[str, Any], file_path: str) -> None:
        """Save data to a YAML file.

        Args:
            data: Dictionary to save as YAML
            file_path: Path where to save the file
        """
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                yaml.dump(
                    data,
                    file,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
        except IOError as e:
            raise YamlSyntaxError(f"Cannot write file: {e}", file_path) from e

    def merge_yamls(self, file_v1_path: str, file_v2_path: str) -> Dict[str, Any]:
        """Merge two YAML files according to configured strategies.

        Args:
            file_v1_path: Path to source YAML file (takes precedence)
            file_v2_path: Path to base YAML file

        Returns:
            Merged YAML data
        """
        v1_data = self.load_yaml_file(file_v1_path)
        v2_data = self.load_yaml_file(file_v2_path)

        self._changes = []

        merged_data = copy.deepcopy(v2_data)
        self._deep_merge(v1_data, merged_data, "")

        if self.deletion_strategy == "remove":
            self._handle_deletions(v1_data, merged_data, "")

        return merged_data

    def _deep_merge(
        self, source: Dict[str, Any], target: Dict[str, Any], path: str
    ) -> None:
        """Recursively merge source into target.

        Args:
            source: Source dictionary (v1_data)
            target: Target dictionary (v2_data, modified in place)
            path: Current path for change tracking
        """
        for key, value in source.items():
            current_path = f"{path}.{key}" if path else key

            if key not in target:
                target[key] = copy.deepcopy(value)
                self._record_change("Added", current_path, None, value)

            elif isinstance(value, dict) and isinstance(target[key], dict):
                self._deep_merge(value, target[key], current_path)

            elif isinstance(value, list) and isinstance(target[key], list):
                new_list = self._merge_lists(value, target[key])
                if new_list != target[key]:
                    self._record_change("Modified", current_path, target[key], new_list)
                    target[key] = new_list

            elif value != target[key]:
                old_value = target[key]
                target[key] = copy.deepcopy(value)
                self._record_change("Modified", current_path, old_value, value)

            else:
                self._record_change("Unchanged", current_path, target[key], value)

    def _merge_lists(self, source_list: List[Any], target_list: List[Any]) -> List[Any]:
        """Merge two lists according to the configured strategy.

        Args:
            source_list: List from source file (v1)
            target_list: List from target file (v2)

        Returns:
            Merged list
        """
        if self.list_merge_strategy == "replace":
            return copy.deepcopy(source_list)

        if self.list_merge_strategy == "append":
            merged_list = copy.deepcopy(target_list)
            merged_list.extend(copy.deepcopy(source_list))
            return merged_list

        if self.list_merge_strategy == "intelligent":
            return self._intelligent_merge_lists(source_list, target_list)

        return copy.deepcopy(source_list)

    def _intelligent_merge_lists(
        self, source_list: List[Any], target_list: List[Any]
    ) -> List[Any]:
        """Intelligently merge lists by matching items with unique identifiers.

        Args:
            source_list: List from source file
            target_list: List from target file

        Returns:
            Intelligently merged list
        """
        if not source_list:
            return copy.deepcopy(target_list)

        if not target_list:
            return copy.deepcopy(source_list)

        merged_list = copy.deepcopy(target_list)

        for source_item in source_list:
            if isinstance(source_item, dict):
                matched_index = self._find_matching_dict_in_list(
                    source_item, merged_list
                )

                if matched_index is not None:
                    if isinstance(merged_list[matched_index], dict):
                        self._deep_merge(source_item, merged_list[matched_index], "")
                    else:
                        merged_list[matched_index] = copy.deepcopy(source_item)
                else:
                    merged_list.append(copy.deepcopy(source_item))

            elif source_item not in merged_list:
                merged_list.append(copy.deepcopy(source_item))

        return merged_list

    def _find_matching_dict_in_list(
        self, target_dict: Dict[str, Any], dict_list: List[Any]
    ) -> Optional[int]:
        """Find a matching dictionary in a list based on common identifier keys.

        Args:
            target_dict: Dictionary to find a match for
            dict_list: List of dictionaries to search in

        Returns:
            Index of matching dictionary, or None if not found
        """
        identifier_keys = ["id", "name", "key", "uuid", "identifier"]

        for key in identifier_keys:
            if key in target_dict:
                for i, item in enumerate(dict_list):
                    if (
                        isinstance(item, dict)
                        and key in item
                        and item[key] == target_dict[key]
                    ):
                        return i

        return None

    def _handle_deletions(
        self, source: Dict[str, Any], target: Dict[str, Any], path: str
    ) -> None:
        """Handle keys present in target but not in source.

        Args:
            source: Source dictionary (v1_data)
            target: Target dictionary (modified in place)
            path: Current path for change tracking
        """
        keys_to_remove = []

        for key in target:
            current_path = f"{path}.{key}" if path else key

            if key not in source:
                keys_to_remove.append(key)
                self._record_change("Removed", current_path, target[key], None)

            elif isinstance(target[key], dict) and isinstance(source[key], dict):
                self._handle_deletions(source[key], target[key], current_path)

        for key in keys_to_remove:
            del target[key]

    def _record_change(
        self, change_type: str, path: str, old_value: Any, new_value: Any
    ) -> None:
        """Record a change for the difference report.

        Args:
            change_type: Type of change ('Added', 'Modified', 'Removed', 'Unchanged')
            path: Path to the changed element
            old_value: Previous value
            new_value: New value
        """
        change_record = {
            "type": change_type,
            "path": path,
            "old_value": old_value,
            "new_value": new_value,
        }
        self._changes.append(change_record)

    def get_changes(self) -> List[Dict[str, Any]]:
        """Get recorded changes from the last merge operation.

        Returns:
            List of change records
        """
        return self._changes.copy()

    def reset_changes(self) -> None:
        """Reset the changes list."""
        self._changes = []
