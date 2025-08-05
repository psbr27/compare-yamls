"""Configuration management for YAML merging operations."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from exceptions import ConfigurationError, FileError


class ConfigManager:
    """Manages configuration loading, validation, and access."""

    DEFAULT_CONFIG = {
        "general_settings": {
            "list_merge_strategy": "replace",
            "handle_deletions": "ignore",
        },
        "input_output": {
            "file_v1_path": "file_v1.yml",
            "file_v2_path": "file_v2.yml",
            "output_final_path": "file_v2_final.yml",
            "diff_report_path": "diff.txt",
        },
        "diff_report_settings": {"show_unchanged_keys": False, "diff_format": "text"},
    }

    VALID_LIST_STRATEGIES = {"replace", "append", "intelligent"}
    VALID_DELETION_STRATEGIES = {"ignore", "remove"}
    VALID_DIFF_FORMATS = {"text", "json"}

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file. Defaults to 'config.json'.
        """
        self.config_path = config_path or "config.json"
        self._config: Dict[str, Any] = {}
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from file or use defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as file:
                    loaded_config = json.load(file)
                self._config = self._merge_with_defaults(loaded_config)
            except json.JSONDecodeError as e:
                raise ConfigurationError(
                    f"Invalid JSON in config file {self.config_path}: {e}"
                ) from e
            except IOError as e:
                raise FileError(
                    f"Cannot read config file {self.config_path}: {e}"
                ) from e
        else:
            self._config = self.DEFAULT_CONFIG.copy()

        self._validate_configuration()

    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded configuration with defaults."""
        merged_config = self.DEFAULT_CONFIG.copy()

        for section_name, section_data in loaded_config.items():
            if section_name in merged_config:
                if isinstance(section_data, dict):
                    merged_config[section_name].update(section_data)
                else:
                    merged_config[section_name] = section_data
            else:
                merged_config[section_name] = section_data

        return merged_config

    def _validate_configuration(self) -> None:
        """Validate configuration values."""
        try:
            general_settings = self._config["general_settings"]

            list_strategy = general_settings["list_merge_strategy"]
            if list_strategy not in self.VALID_LIST_STRATEGIES:
                raise ConfigurationError(
                    f"Invalid list_merge_strategy: {list_strategy}. "
                    f"Valid options: {', '.join(self.VALID_LIST_STRATEGIES)}"
                )

            deletion_strategy = general_settings["handle_deletions"]
            if deletion_strategy not in self.VALID_DELETION_STRATEGIES:
                raise ConfigurationError(
                    f"Invalid handle_deletions: {deletion_strategy}. "
                    f"Valid options: {', '.join(self.VALID_DELETION_STRATEGIES)}"
                )

            diff_format = self._config["diff_report_settings"]["diff_format"]
            if diff_format not in self.VALID_DIFF_FORMATS:
                raise ConfigurationError(
                    f"Invalid diff_format: {diff_format}. "
                    f"Valid options: {', '.join(self.VALID_DIFF_FORMATS)}"
                )

        except KeyError as e:
            raise ConfigurationError(f"Missing required configuration key: {e}") from e

    def get_list_merge_strategy(self) -> str:
        """Get the list merge strategy."""
        return self._config["general_settings"]["list_merge_strategy"]

    def get_deletion_strategy(self) -> str:
        """Get the deletion handling strategy."""
        return self._config["general_settings"]["handle_deletions"]

    def get_file_v1_path(self) -> str:
        """Get the path to file_v1.yml."""
        return self._config["input_output"]["file_v1_path"]

    def get_file_v2_path(self) -> str:
        """Get the path to file_v2.yml."""
        return self._config["input_output"]["file_v2_path"]

    def get_output_final_path(self) -> str:
        """Get the path for the final merged output file."""
        return self._config["input_output"]["output_final_path"]

    def get_diff_report_path(self) -> str:
        """Get the path for the difference report file."""
        return self._config["input_output"]["diff_report_path"]

    def show_unchanged_keys(self) -> bool:
        """Check if unchanged keys should be shown in the report."""
        return self._config["diff_report_settings"]["show_unchanged_keys"]

    def get_diff_format(self) -> str:
        """Get the difference report format."""
        return self._config["diff_report_settings"]["diff_format"]

    # Site Configuration Methods
    def get_cncc_id(self) -> str:
        """Get the CNCC ID for the site."""
        return self._config.get("site_configuration", {}).get("cncc_id", "ocslf")

    def get_cluster_domain(self) -> str:
        """Get the cluster domain."""
        return self._config.get("site_configuration", {}).get("cluster_domain", "cluster.local")

    def get_docker_registry(self) -> str:
        """Get the Docker registry."""
        return self._config.get("site_configuration", {}).get("docker_registry", "occne-repo-host:5000")

    def get_service_account_name(self) -> str:
        """Get the service account name."""
        return self._config.get("site_configuration", {}).get("service_account_name", "ocslf-serviceaccount")

    def get_helm_test_service_account_name(self) -> str:
        """Get the Helm test service account name."""
        return self._config.get("site_configuration", {}).get("helm_test_service_account_name", "ocslf-serviceaccount")

    # Network Configuration Methods
    def get_static_ip_addresses(self) -> Dict[str, str]:
        """Get static IP addresses configuration."""
        return self._config.get("network_configuration", {}).get("static_ip_addresses", {})

    def get_ports(self) -> Dict[str, int]:
        """Get port configurations."""
        return self._config.get("network_configuration", {}).get("ports", {})

    def get_metallb_pool(self) -> str:
        """Get the MetalLB pool name."""
        return self._config.get("network_configuration", {}).get("metallb_pool", "default")

    # Database Configuration Methods
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self._config.get("database_configuration", {})

    def get_database_names(self) -> Dict[str, str]:
        """Get database names with site-specific suffixes."""
        return self._config.get("database_configuration", {}).get("names", {})

    # Custom Labels Methods
    def get_custom_labels(self) -> Dict[str, str]:
        """Get custom labels configuration."""
        return self._config.get("custom_labels", {})

    # Environment Configuration Methods
    def get_environment_config(self) -> Dict[str, str]:
        """Get environment configuration."""
        return self._config.get("environment_configuration", {})

    # Version Management Methods
    def get_version_management_config(self) -> Dict[str, Any]:
        """Get version management configuration."""
        return self._config.get("version_management", {})

    def should_preserve_versions_from_v2(self) -> bool:
        """Check if versions should be preserved from v2 file."""
        return self._config.get("version_management", {}).get("preserve_versions_from_v2", True)

    def get_version_patterns_to_skip(self) -> list:
        """Get version patterns that should be skipped during merge."""
        return self._config.get("version_management", {}).get("version_patterns_to_skip", [])

    def get_version_mappings(self) -> Dict[str, str]:
        """Get version mappings for corrections."""
        return self._config.get("version_management", {}).get("version_mappings", {})

    def get_special_version_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get special version mappings for specific components."""
        return self._config.get("version_management", {}).get("special_version_mappings", {})

    # Instance Configuration Methods
    def get_instance_configurations(self) -> Dict[str, Any]:
        """Get instance configurations."""
        return self._config.get("instance_configurations", {})

    # Merge Strategy Methods
    def get_merge_strategy_config(self) -> Dict[str, bool]:
        """Get merge strategy configuration."""
        return self._config.get("merge_strategy", {})

    def should_preserve_v2_versions(self) -> bool:
        """Check if v2 versions should be preserved."""
        return self._config.get("merge_strategy", {}).get("preserve_v2_versions", True)

    def should_preserve_site_specific_values(self) -> bool:
        """Check if site-specific values should be preserved."""
        return self._config.get("merge_strategy", {}).get("preserve_site_specific_values", True)

    def should_skip_version_fields(self) -> bool:
        """Check if version fields should be skipped."""
        return self._config.get("merge_strategy", {}).get("skip_version_fields", True)

    def should_apply_custom_labels(self) -> bool:
        """Check if custom labels should be applied."""
        return self._config.get("merge_strategy", {}).get("apply_custom_labels", True)

    def should_apply_environment_config(self) -> bool:
        """Check if environment configuration should be applied."""
        return self._config.get("merge_strategy", {}).get("apply_environment_config", True)

    def override_setting(self, key_path: str, value: Any) -> None:
        """Override a configuration setting.

        Args:
            key_path: Dot-separated path to the setting
                     (e.g., 'general_settings.list_merge_strategy')
            value: New value for the setting
        """
        keys = key_path.split(".")
        current = self._config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
        self._validate_configuration()

    def validate_file_paths(self) -> None:
        """Validate that input files exist and output directories are writable."""
        v1_path = Path(self.get_file_v1_path())
        v2_path = Path(self.get_file_v2_path())
        output_path = Path(self.get_output_final_path())
        diff_path = Path(self.get_diff_report_path())

        if not v1_path.exists():
            raise FileError(f"Input file does not exist: {v1_path}")

        if not v2_path.exists():
            raise FileError(f"Input file does not exist: {v2_path}")

        if not v1_path.is_file():
            raise FileError(f"Path is not a file: {v1_path}")

        if not v2_path.is_file():
            raise FileError(f"Path is not a file: {v2_path}")

        output_dir = output_path.parent
        diff_dir = diff_path.parent

        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise FileError(
                    f"Cannot create output directory {output_dir}: {e}"
                ) from e

        if not diff_dir.exists():
            try:
                diff_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise FileError(
                    f"Cannot create diff report directory {diff_dir}: {e}"
                ) from e

        if not os.access(output_dir, os.W_OK):
            raise FileError(f"Output directory is not writable: {output_dir}")

        if not os.access(diff_dir, os.W_OK):
            raise FileError(f"Diff report directory is not writable: {diff_dir}")

    def get_full_config(self) -> Dict[str, Any]:
        """Get the complete configuration dictionary."""
        return self._config.copy()
