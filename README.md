# YAML Merger

A powerful, object-oriented YAML file comparison and merging tool with intelligent merge strategies and comprehensive difference reporting.

## Features

- **Deep YAML Merging**: Recursively merge complex nested YAML structures
- **Multiple Merge Strategies**: Choose from replace, append, or intelligent list merging
- **Flexible Deletion Handling**: Ignore or remove deleted keys during merge operations
- **Comprehensive Reporting**: Generate detailed difference reports in text or JSON format
- **Binary Distribution**: Compile to standalone executables with PyInstaller
- **Extensive Configuration**: JSON-based configuration with CLI override support
- **Strict OOP Design**: Clean, maintainable object-oriented architecture
- **High Code Quality**: 9.87/10 pylint score with comprehensive test coverage

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/psbr27/compare-yamls.git
cd compare-yamls
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Binary Distribution

Build standalone executables:
```bash
./build_binary.sh
```

This creates:
- `dist/generateFinalYml` - Standalone executable
- `dist/generateFinalYml_with_internal/` - Directory with dependencies

## Usage

### Basic Usage

```bash
# Merge two YAML files
python merge_yaml.py file_v1.yml file_v2.yml

# Use intelligent list merging
python merge_yaml.py --list-merge-strategy=intelligent file_v1.yml file_v2.yml

# Generate JSON difference report
python merge_yaml.py --diff-format=json file_v1.yml file_v2.yml

# Use custom configuration
python merge_yaml.py --config=my_config.json file_v1.yml file_v2.yml
```

### Command Line Options

```
usage: merge_yaml.py [-h] [--version] [-v] [--output OUTPUT]
                     [--list-merge-strategy {replace,append,intelligent}]
                     [--handle-deletions {ignore,remove}]
                     [--diff-format {text,json}] [--config CONFIG]
                     source_file target_file

Advanced YAML file comparison and merging tool

positional arguments:
  source_file           Source YAML file path
  target_file           Target YAML file to merge into

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -v, --verbose-version
                        show detailed version information and exit
  --output OUTPUT       Output file path (default: file_v2_final.yml)
  --list-merge-strategy {replace,append,intelligent}
                        Strategy for merging lists (default: replace)
  --handle-deletions {ignore,remove}
                        How to handle deleted keys (default: ignore)
  --diff-format {text,json}
                        Format for difference reports (default: text)
  --config CONFIG       Path to configuration file (default: config.json)
```

### Configuration

Create a `config.json` file to customize default behavior:

```json
{
  "general_settings": {
    "list_merge_strategy": "intelligent",
    "handle_deletions": "ignore"
  },
  "output_settings": {
    "default_output_file": "merged_output.yml",
    "generate_diff_report": true,
    "diff_report_format": "text"
  },
  "merge_strategies": {
    "database": {
      "list_merge_strategy": "append",
      "handle_deletions": "remove"
    }
  }
}
```

## Merge Strategies

### List Merge Strategies

- **replace** (default): Replace target list with source list
- **append**: Append source list items to target list
- **intelligent**: Smart merging based on item structure and keys

### Deletion Handling

- **ignore** (default): Keep deleted keys in final output
- **remove**: Remove keys that exist in target but not in source

## Examples

### Example 1: Basic Merge

**file_v1.yml:**
```yaml
database:
  host: localhost
  port: 5432
  users:
    - name: admin
      role: administrator
```

**file_v2.yml:**
```yaml
database:
  host: production.db
  timeout: 30
  users:
    - name: user1
      role: user
```

**Result:**
```yaml
database:
  host: localhost  # Source takes precedence
  port: 5432       # Preserved from source
  timeout: 30      # Added from target
  users:           # Replaced with source (default strategy)
    - name: admin
      role: administrator
```

### Example 2: Intelligent List Merging

```bash
python merge_yaml.py --list-merge-strategy=intelligent file_v1.yml file_v2.yml
```

**Result:**
```yaml
database:
  host: localhost
  port: 5432
  timeout: 30
  users:           # Intelligently merged
    - name: admin
      role: administrator
    - name: user1
      role: user
```

## Development

### Prerequisites

- Python 3.8+
- Virtual environment recommended

### Setup Development Environment

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests
python -m pytest tests/

# Run linting
pylint *.py
black --check .
isort --check-only .
```

### Code Quality

The project maintains high code quality standards:
- **Black** for code formatting
- **isort** for import sorting
- **Pylint** for linting (9.87/10 score)
- **Shellcheck** for shell script validation
- **Pre-commit hooks** for automated quality checks

### Building Binaries

```bash
# Build standalone executable
./build_binary.sh

# Test binary
./dist/generateFinalYml --help
./dist/generateFinalYml --version
```

## Architecture

### Core Classes

- **YamlMerger**: Main merging logic with configurable strategies
- **ConfigManager**: Configuration loading and validation
- **DiffReporter**: Difference analysis and report generation
- **Custom Exceptions**: Comprehensive error handling hierarchy

### Design Principles

- Strict object-oriented programming
- Single responsibility principle
- Comprehensive error handling
- Extensive configuration support
- Clean separation of concerns

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_yaml_merger.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow code quality standards (pre-commit hooks will help)
4. Write tests for new functionality
5. Submit a pull request

### Code Style

- Follow PEP 8 standards
- Use type hints where appropriate
- Maintain 100-character line length
- Write comprehensive docstrings
- Achieve minimum 9.8/10 pylint score

## License

MIT License - see LICENSE file for details.

## Version Information

Get detailed version information:

```bash
# Short version
python merge_yaml.py --version

# Detailed version with build info
python merge_yaml.py -v
```

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check existing documentation
- Review test examples for usage patterns