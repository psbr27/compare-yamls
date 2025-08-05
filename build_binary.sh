#!/bin/bash

# YAML Merger Binary Build Script
# Compiles the YAML merger application into a standalone binary using PyInstaller

set -e  # Exit on any error

echo "🔨 Building YAML Merger Binary with PyInstaller"
echo "================================================"

# Configuration
BINARY_NAME="generateFinalYml"
MAIN_SCRIPT="merge_yaml.py"
BUILD_DIR="build"
DIST_DIR="dist"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment is activated
check_venv() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "Virtual environment not detected. Activating venv..."
        if [[ -d "venv" ]]; then
            source venv/bin/activate
            print_success "Virtual environment activated"
        else
            print_error "Virtual environment not found. Please run: python3 -m venv venv"
            exit 1
        fi
    else
        print_success "Virtual environment detected: $VIRTUAL_ENV"
    fi
}

# Install PyInstaller if not already installed
install_pyinstaller() {
    print_status "Checking for PyInstaller..."
    if ! python -c "import PyInstaller" 2>/dev/null; then
        print_status "Installing PyInstaller..."
        pip install PyInstaller
        print_success "PyInstaller installed"
    else
        print_success "PyInstaller already installed"
    fi
}

# Clean previous builds
clean_builds() {
    print_status "Cleaning previous builds..."
    rm -rf "$BUILD_DIR" "$DIST_DIR" ./*.spec
    print_success "Previous builds cleaned"
}

# Verify all required files exist
verify_files() {
    print_status "Verifying required files..."

    required_files=(
        "$MAIN_SCRIPT"
        "config_manager.py"
        "yaml_merger.py"
        "diff_reporter.py"
        "exceptions.py"
        "config.json"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_error "Required file missing: $file"
            exit 1
        fi
    done

    print_success "All required files found"
}

# Update build information
update_build_info() {
    print_status "Updating build information..."

    # Get current timestamp
    BUILD_DATE=$(date '+%Y-%m-%d')
    BUILD_TIME=$(date '+%H:%M:%S')
    # shellcheck disable=SC2034
    BUILD_USER=$(whoami)
    # shellcheck disable=SC2034
    BUILD_HOST=$(hostname)

    # Get Python version info
    PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")

    # Update version_info.py with actual build information
    sed -i.bak "s/BUILD_DATE = \".*\"/BUILD_DATE = \"$BUILD_DATE\"/" version_info.py
    sed -i.bak "s/BUILD_TIME = \".*\"/BUILD_TIME = \"$BUILD_TIME\"/" version_info.py
    sed -i.bak "s/BUILD_PYTHON_VERSION = \".*\"/BUILD_PYTHON_VERSION = \"$PYTHON_VERSION\"/" version_info.py

    # Clean up backup file
    rm -f version_info.py.bak

    print_success "Build information updated"
}

# Build the binary
build_binary() {
    print_status "Building binary with PyInstaller..."

    # PyInstaller command with optimized settings
    if pyinstaller \
        --onefile \
        --name="$BINARY_NAME" \
        --add-data="config.json:." \
        --hidden-import="yaml" \
        --hidden-import="argparse" \
        --hidden-import="json" \
        --hidden-import="pathlib" \
        --hidden-import="datetime" \
        --hidden-import="subprocess" \
        --hidden-import="platform" \
        --hidden-import="version_info" \
        --clean \
        --noconfirm \
        "$MAIN_SCRIPT"; then
        print_success "Binary built successfully"
    else
        print_error "Binary build failed"
        exit 1
    fi
}

# Create _internal directory structure (for PyInstaller onedir mode as alternative)
create_onedir_build() {
    print_status "Creating alternative onedir build with _internal structure..."

    # Build with onedir mode
    # shellcheck disable=SC2034
    if command_output=$(pyinstaller \
        --onedir \
        --name="${BINARY_NAME}_dir" \
        --add-data="config.json:." \
        --hidden-import="yaml" \
        --hidden-import="argparse" \
        --hidden-import="json" \
        --hidden-import="pathlib" \
        --hidden-import="datetime" \
        --hidden-import="subprocess" \
        --hidden-import="platform" \
        --hidden-import="version_info" \
        --clean \
        --noconfirm \
        "$MAIN_SCRIPT" 2>&1); then
        print_success "Onedir build created successfully"

        # Rename the internal directory to _internal for consistency
        if [[ -d "$DIST_DIR/${BINARY_NAME}_dir" ]]; then
            mv "$DIST_DIR/${BINARY_NAME}_dir" "$DIST_DIR/${BINARY_NAME}_with_internal"
            if [[ -d "$DIST_DIR/${BINARY_NAME}_with_internal/_internal" ]]; then
                print_success "_internal directory structure created"
            fi
        fi
    else
        print_warning "Onedir build failed, continuing with onefile build only"
    fi
}

# Verify the binary works
test_binary() {
    print_status "Testing the generated binary..."

    binary_path="$DIST_DIR/$BINARY_NAME"

    if [[ -f "$binary_path" ]]; then
        # Test help command
        if "$binary_path" --help > /dev/null 2>&1; then
            print_success "Binary test passed - help command works"
        else
            print_error "Binary test failed - help command failed"
            exit 1
        fi

        # Test version command
        if "$binary_path" --version > /dev/null 2>&1; then
            print_success "Binary test passed - version command works"
        else
            print_warning "Version command test failed (non-critical)"
        fi

        # Test verbose version command
        if "$binary_path" -v > /dev/null 2>&1; then
            print_success "Binary test passed - verbose version command works"
        else
            print_warning "Verbose version command test failed (non-critical)"
        fi
    else
        print_error "Binary not found at expected location: $binary_path"
        exit 1
    fi
}

# Display build information
show_build_info() {
    print_success "Build completed successfully!"
    echo
    echo "📦 Build Information:"
    echo "===================="
    echo "Binary name: $BINARY_NAME"
    echo "Main script: $MAIN_SCRIPT"
    echo

    if [[ -f "$DIST_DIR/$BINARY_NAME" ]]; then
        binary_size=$(du -h "$DIST_DIR/$BINARY_NAME" | cut -f1)
        echo "📁 Standalone Binary:"
        echo "   Location: $DIST_DIR/$BINARY_NAME"
        echo "   Size: $binary_size"
        echo "   Usage: ./$DIST_DIR/$BINARY_NAME [options]"
        echo
    fi

    if [[ -d "$DIST_DIR/${BINARY_NAME}_with_internal" ]]; then
        echo "📁 Directory Build (with _internal):"
        echo "   Location: $DIST_DIR/${BINARY_NAME}_with_internal/"
        echo "   Executable: $DIST_DIR/${BINARY_NAME}_with_internal/${BINARY_NAME}_dir"
        echo "   Libraries: $DIST_DIR/${BINARY_NAME}_with_internal/_internal/"
        echo
    fi

    echo "🚀 Example usage:"
    echo "   ./$DIST_DIR/$BINARY_NAME --help"
    echo "   ./$DIST_DIR/$BINARY_NAME --version"
    echo "   ./$DIST_DIR/$BINARY_NAME -v                    # Detailed version info"
    echo "   ./$DIST_DIR/$BINARY_NAME --list-merge-strategy=intelligent"
    echo "   ./$DIST_DIR/$BINARY_NAME --config=my_config.json"
}

# Main execution
main() {
    print_status "Starting YAML Merger binary build process..."

    check_venv
    install_pyinstaller
    verify_files
    update_build_info
    clean_builds
    build_binary
    create_onedir_build
    test_binary
    show_build_info

    print_success "All done! 🎉"
}

# Run main function
main "$@"
