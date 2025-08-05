"""Version and build information for YAML Merger."""

import os
import platform
import sys

import yaml

# Application metadata
APP_NAME = "YAML Merger"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Advanced YAML file comparison and merging tool"
APP_AUTHOR = "Claude Code Assistant"
APP_LICENSE = "MIT"

# Build information (will be updated by build script)
BUILD_DATE = "2025-08-05"
BUILD_TIME = "14:20:54"
BUILD_USER = os.getenv("USER", "unknown")
BUILD_HOST = platform.node()
BUILD_PYTHON_VERSION = (
    f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
)


# Git information (if available)
def get_git_info():
    """Get git commit information if available."""
    try:
        import subprocess

        # Get current commit hash
        commit_hash = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()[:8]
        )

        # Get current branch
        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )

        # Get commit date
        commit_date = (
            subprocess.check_output(
                ["git", "log", "-1", "--format=%ci"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )

        return {"commit": commit_hash, "branch": branch, "date": commit_date}
    except (subprocess.CalledProcessError, FileNotFoundError, ImportError):
        return None


# Package versions
def get_package_versions():
    """Get versions of key dependencies."""
    packages = {}

    try:
        packages["pyyaml"] = yaml.__version__
    except AttributeError:
        packages["pyyaml"] = "unknown"

    # Standard library modules (no version info)
    stdlib_modules = ["argparse", "json", "pathlib", "datetime", "copy", "os", "sys"]
    for module in stdlib_modules:
        packages[module] = f"stdlib (Python {BUILD_PYTHON_VERSION})"

    return packages


def get_system_info():
    """Get system information."""
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "architecture": platform.architecture()[0],
        "python_version": sys.version,
        "python_executable": sys.executable,
    }


def get_build_info():
    """Get comprehensive build information."""
    git_info = get_git_info()
    packages = get_package_versions()
    system_info = get_system_info()

    # Calculate binary size if running as compiled binary
    binary_size = "unknown"
    try:
        if getattr(sys, "frozen", False):
            # Running as compiled binary
            binary_path = sys.executable
            binary_size = f"{os.path.getsize(binary_path) / (1024*1024):.1f} MB"
    except (OSError, AttributeError):
        pass

    build_info = {
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "description": APP_DESCRIPTION,
            "author": APP_AUTHOR,
            "license": APP_LICENSE,
        },
        "build": {
            "date": BUILD_DATE,
            "time": BUILD_TIME,
            "user": BUILD_USER,
            "host": BUILD_HOST,
            "python_version": BUILD_PYTHON_VERSION,
            "binary_size": binary_size,
            "frozen": getattr(sys, "frozen", False),
        },
        "git": git_info,
        "packages": packages,
        "system": system_info,
        "runtime": {
            "python_path": sys.path[0] if sys.path else "unknown",
            "working_directory": os.getcwd(),
            "executable": sys.executable,
            "platform": sys.platform,
        },
    }

    return build_info


def print_version_info():
    """Print comprehensive version information."""
    build_info = get_build_info()

    print(f"{build_info['app']['name']} v{build_info['app']['version']}")
    print("=" * 60)
    print(f"Description: {build_info['app']['description']}")
    print(f"Author: {build_info['app']['author']}")
    print(f"License: {build_info['app']['license']}")
    print()

    # Build Information
    print("Build Information:")
    print("-" * 30)
    print(f"Build Date: {build_info['build']['date']} {build_info['build']['time']}")
    print(f"Built by: {build_info['build']['user']}@{build_info['build']['host']}")
    print(f"Python Version: {build_info['build']['python_version']}")
    print(f"Binary Size: {build_info['build']['binary_size']}")
    print(f"Frozen Binary: {'Yes' if build_info['build']['frozen'] else 'No'}")
    print()

    # Git Information
    if build_info["git"]:
        print("Git Information:")
        print("-" * 30)
        print(f"Commit: {build_info['git']['commit']}")
        print(f"Branch: {build_info['git']['branch']}")
        print(f"Commit Date: {build_info['git']['date']}")
        print()

    # Package Versions
    print("Package Versions:")
    print("-" * 30)
    for package, version in sorted(build_info["packages"].items()):
        print(f"{package:15} : {version}")
    print()

    # System Information
    print("System Information:")
    print("-" * 30)
    print(f"Platform: {build_info['system']['platform']}")
    print(f"System: {build_info['system']['system']}")
    print(f"Architecture: {build_info['system']['architecture']}")
    print(f"Machine: {build_info['system']['machine']}")
    print(f"Processor: {build_info['system']['processor']}")
    print()

    # Runtime Information
    print("Runtime Information:")
    print("-" * 30)
    print(f"Python Executable: {build_info['runtime']['executable']}")
    print(f"Working Directory: {build_info['runtime']['working_directory']}")
    print(f"Python Path: {build_info['runtime']['python_path']}")
    print(f"Platform: {build_info['runtime']['platform']}")


def get_short_version():
    """Get short version string for --version."""
    build_info = get_build_info()
    version_str = f"{build_info['app']['name']} {build_info['app']['version']}"

    if build_info["git"]:
        version_str += f" ({build_info['git']['commit']})"

    version_str += f" - Built on {build_info['build']['date']}"

    if build_info["build"]["frozen"]:
        version_str += " [Compiled Binary]"

    return version_str


if __name__ == "__main__":
    print_version_info()
