#!/usr/bin/env python3
"""Main entry point for YAML merge operations."""

import argparse
import sys
from typing import Optional

from config_manager import ConfigManager
from diff_reporter import DiffReporter
from exceptions import YamlMergeError
from version_info import get_short_version, print_version_info
from yaml_merger import YamlMerger


class YamlMergeApplication:
    """Main application class for YAML merging operations."""

    def __init__(self) -> None:
        """Initialize the application."""
        self.config_manager: Optional[ConfigManager] = None
        self.yaml_merger: Optional[YamlMerger] = None
        self.diff_reporter: Optional[DiffReporter] = None

    def run(self, args: argparse.Namespace) -> int:
        """Run the YAML merge application.

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            self._initialize_components(args)
            self._validate_environment()
            merged_data = self._perform_merge()
            self._generate_reports(merged_data)

            print("YAML merge completed successfully!")
            return 0

        except YamlMergeError as e:
            print(f"Error: {e}", file=sys.stderr)
            return e.exit_code

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1

    def _initialize_components(self, args: argparse.Namespace) -> None:
        """Initialize application components with configuration.

        Args:
            args: Parsed command line arguments
        """
        config_path = getattr(args, "config", None)
        self.config_manager = ConfigManager(config_path)

        self._apply_cli_overrides(args)

        # Initialize YamlMerger with config manager
        self.yaml_merger = YamlMerger(self.config_manager)

        self.diff_reporter = DiffReporter(
            show_unchanged=self.config_manager.show_unchanged_keys(),
            format_type=self.config_manager.get_diff_format(),
        )

    def _apply_cli_overrides(self, args: argparse.Namespace) -> None:
        """Apply command line argument overrides to configuration.

        Args:
            args: Parsed command line arguments
        """
        assert self.config_manager is not None
        
        overrides = [
            ("list_merge_strategy", "general_settings.list_merge_strategy"),
            ("handle_deletions", "general_settings.handle_deletions"),
            ("file_v1_path", "input_output.file_v1_path"),
            ("file_v2_path", "input_output.file_v2_path"),
            ("output_final_path", "input_output.output_final_path"),
            ("diff_report_path", "input_output.diff_report_path"),
            ("show_unchanged_keys", "diff_report_settings.show_unchanged_keys"),
            ("diff_format", "diff_report_settings.diff_format"),
        ]

        for arg_name, config_path in overrides:
            value = getattr(args, arg_name, None)
            if value is not None:
                self.config_manager.override_setting(config_path, value)

    def _validate_environment(self) -> None:
        """Validate the environment and file paths."""
        assert self.config_manager is not None
        self.config_manager.validate_file_paths()

    def _perform_merge(self) -> dict:
        """Perform the YAML merge operation.

        Returns:
            Merged YAML data
        """
        assert self.config_manager is not None
        assert self.yaml_merger is not None
        
        v1_path = self.config_manager.get_file_v1_path()
        v2_path = self.config_manager.get_file_v2_path()
        output_path = self.config_manager.get_output_final_path()

        merged_data = self.yaml_merger.merge_yamls(v1_path, v2_path)
        self.yaml_merger.save_yaml_file(merged_data, output_path)

        return merged_data

    def _generate_reports(
        self, merged_data: dict  # pylint: disable=unused-argument
    ) -> None:
        """Generate difference reports.

        Args:
            merged_data: Merged YAML data
        """
        assert self.yaml_merger is not None
        assert self.diff_reporter is not None
        assert self.config_manager is not None
        
        changes = self.yaml_merger.get_changes()
        diff_path = self.config_manager.get_diff_report_path()

        self.diff_reporter.generate_report(changes, diff_path)

        summary = self.diff_reporter.get_changes_summary(changes)
        print(
            f"Changes summary: Added: {summary['Added']}, "
            f"Modified: {summary['Modified']}, Removed: {summary['Removed']}"
        )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command line argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Merge two YAML files with configurable strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Use default config.json
  %(prog)s --list-merge-strategy=append      # Override merge strategy
  %(prog)s --config=custom.json              # Use custom config file
  %(prog)s --handle-deletions=remove         # Remove keys absent in v1
        """,
    )

    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to configuration file (default: config.json)",
    )

    parser.add_argument(
        "--list-merge-strategy",
        choices=["replace", "append", "intelligent"],
        help="Strategy for merging lists",
    )

    parser.add_argument(
        "--handle-deletions",
        choices=["ignore", "remove"],
        help="How to handle keys present only in v2",
    )

    parser.add_argument(
        "--file-v1-path", metavar="PATH", help="Path to source YAML file (v1)"
    )

    parser.add_argument(
        "--file-v2-path", metavar="PATH", help="Path to base YAML file (v2)"
    )

    parser.add_argument(
        "--output-final-path", metavar="PATH", help="Path for merged output file"
    )

    parser.add_argument(
        "--diff-report-path", metavar="PATH", help="Path for difference report"
    )

    parser.add_argument(
        "--show-unchanged-keys",
        action="store_true",
        help="Include unchanged keys in difference report",
    )

    parser.add_argument(
        "--diff-format", choices=["text", "json"], help="Format for difference report"
    )

    # Version arguments
    parser.add_argument("--version", action="version", version=get_short_version())

    parser.add_argument(
        "-v",
        "--verbose-version",
        action="store_true",
        help="Show detailed version and build information",
    )

    return parser


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    parser = create_argument_parser()
    args = parser.parse_args()

    # Handle verbose version info
    if getattr(args, "verbose_version", False):
        print_version_info()
        return 0

    application = YamlMergeApplication()
    return application.run(args)


if __name__ == "__main__":
    sys.exit(main())
