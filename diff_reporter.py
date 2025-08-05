"""Difference report generation for YAML merge operations."""

import json
from datetime import datetime
from typing import Any, Dict, List

from exceptions import FileError


class DiffReporter:
    """Generates difference reports in various formats."""

    def __init__(self, show_unchanged: bool = False, format_type: str = "text") -> None:
        """Initialize difference reporter.

        Args:
            show_unchanged: Whether to include unchanged keys in report
            format_type: Output format ('text' or 'json')
        """
        self.show_unchanged = show_unchanged
        self.format_type = format_type

    def generate_report(self, changes: List[Dict[str, Any]], output_path: str) -> None:
        """Generate and save difference report.

        Args:
            changes: List of change records from YamlMerger
            output_path: Path to save the report
        """
        if self.format_type == "json":
            self._generate_json_report(changes, output_path)
        else:
            self._generate_text_report(changes, output_path)

    def _generate_text_report(
        self, changes: List[Dict[str, Any]], output_path: str
    ) -> None:
        """Generate a human-readable text report.

        Args:
            changes: List of change records
            output_path: Path to save the report
        """
        try:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write("YAML Merge Difference Report\n")
                file.write("=" * 50 + "\n")
                file.write(
                    f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                filtered_changes = self._filter_changes(changes)

                if not filtered_changes:
                    file.write("No changes detected.\n")
                    return

                summary = self._generate_summary(filtered_changes)
                file.write("Summary:\n")
                file.write("-" * 20 + "\n")
                for change_type, count in summary.items():
                    if count > 0:
                        file.write(f"{change_type}: {count}\n")
                file.write("\n")

                grouped_changes = self._group_changes_by_type(filtered_changes)

                for change_type in ["Added", "Modified", "Removed"]:
                    if change_type in grouped_changes:
                        file.write(f"{change_type} Keys:\n")
                        file.write("-" * (len(change_type) + 6) + "\n")

                        for change in grouped_changes[change_type]:
                            self._write_text_change(file, change)

                        file.write("\n")

                if self.show_unchanged and "Unchanged" in grouped_changes:
                    file.write("Unchanged Keys:\n")
                    file.write("-" * 16 + "\n")
                    for change in grouped_changes["Unchanged"]:
                        file.write(f"Path: {change['path']}\n")
                        file.write(
                            f"Value: {self._format_value(change['old_value'])}\n\n"
                        )

        except IOError as e:
            raise FileError(f"Cannot write report to {output_path}: {e}") from e

    def _generate_json_report(
        self, changes: List[Dict[str, Any]], output_path: str
    ) -> None:
        """Generate a machine-readable JSON report.

        Args:
            changes: List of change records
            output_path: Path to save the report
        """
        try:
            filtered_changes = self._filter_changes(changes)

            report_data = {
                "metadata": {
                    "generated_on": datetime.now().isoformat(),
                    "format_version": "1.0",
                    "show_unchanged": self.show_unchanged,
                },
                "summary": self._generate_summary(filtered_changes),
                "changes": [],
            }

            for change in filtered_changes:
                change_data = {
                    "type": change["type"],
                    "path": change["path"],
                    "old_value": change["old_value"],
                    "new_value": change["new_value"],
                }
                report_data["changes"].append(change_data)

            with open(output_path, "w", encoding="utf-8") as file:
                json.dump(
                    report_data,
                    file,
                    indent=2,
                    ensure_ascii=False,
                    default=self._json_serializer,
                )

        except IOError as e:
            raise FileError(f"Cannot write report to {output_path}: {e}") from e

    def _filter_changes(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter changes based on show_unchanged setting.

        Args:
            changes: List of all change records

        Returns:
            Filtered list of changes
        """
        if self.show_unchanged:
            return changes

        return [change for change in changes if change["type"] != "Unchanged"]

    def _generate_summary(self, changes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Generate summary statistics for changes.

        Args:
            changes: List of change records

        Returns:
            Dictionary with change type counts
        """
        summary = {"Added": 0, "Modified": 0, "Removed": 0, "Unchanged": 0}

        for change in changes:
            change_type = change["type"]
            if change_type in summary:
                summary[change_type] += 1

        return summary

    def _group_changes_by_type(
        self, changes: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group changes by their type.

        Args:
            changes: List of change records

        Returns:
            Dictionary with changes grouped by type
        """
        grouped = {}

        for change in changes:
            change_type = change["type"]
            if change_type not in grouped:
                grouped[change_type] = []
            grouped[change_type].append(change)

        return grouped

    def _write_text_change(self, file, change: Dict[str, Any]) -> None:
        """Write a single change to the text report.

        Args:
            file: File object to write to
            change: Change record
        """
        file.write(f"Path: {change['path']}\n")

        if change["type"] == "Added":
            file.write(f"New Value: {self._format_value(change['new_value'])}\n")

        elif change["type"] == "Modified":
            file.write(f"Old Value: {self._format_value(change['old_value'])}\n")
            file.write(f"New Value: {self._format_value(change['new_value'])}\n")

        elif change["type"] == "Removed":
            file.write(f"Removed Value: {self._format_value(change['old_value'])}\n")

        file.write("\n")

    def _format_value(self, value: Any) -> str:
        """Format a value for display in text report.

        Args:
            value: Value to format

        Returns:
            Formatted string representation
        """
        if value is None:
            return "null"

        if isinstance(value, str):
            if len(value) > 100:
                return f'"{value[:97]}..."'
            return f'"{value}"'

        if isinstance(value, (list, dict)):
            value_str = str(value)
            if len(value_str) > 200:
                return f"{value_str[:197]}..."
            return value_str

        return str(value)

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for non-standard types.

        Args:
            obj: Object to serialize

        Returns:
            Serializable representation
        """
        if isinstance(obj, datetime):
            return obj.isoformat()

        return str(obj)

    def get_changes_summary(self, changes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get a summary of changes without generating a full report.

        Args:
            changes: List of change records

        Returns:
            Summary statistics
        """
        filtered_changes = self._filter_changes(changes)
        return self._generate_summary(filtered_changes)
