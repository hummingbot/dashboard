#!/bin/bash

# Script to build, copy and install a Python wheel package from a source directory to a destination directory

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --force-repackage           Force rebuilding the wheel package"
    echo "  --source-dir=DIR            Source directory containing the Python package (default: ../hummingbot)"
    echo "  --dest-dir=DIR              Destination directory for the wheel file (default: ./wheels)"
    echo "  --package-name=NAME         Name of the package to build (default: hummingbot)"
    echo "  --conda-env=NAME            Conda environment to install into (required if not in environment.yml or .env)"
    echo "  --build-env=NAME            Conda environment to build the package in (default: hummingbot)"
    echo "  --help                      Show this help message"
    echo ""
    echo "When called from Makefile, you can use this format for arguments not in the makefile:"
    echo "make reference-local-hummingbot ARGS=\"--force-repackage --source-dir=DIR ...\""
}

# Default values
FORCE_REPACKAGE=false
SOURCE_DIR=""
DEST_DIR=""
PACKAGE_NAME="hummingbot"
CONDA_ENV=""
BUILD_ENV="hummingbot"

# Get current working directory
CWD="$(pwd)"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force-repackage)
            FORCE_REPACKAGE=true
            shift
            ;;
        --source-dir=*)
            SOURCE_DIR="${1#*=}"
            shift
            ;;
        --dest-dir=*)
            DEST_DIR="${1#*=}"
            shift
            ;;
        --package-name=*)
            PACKAGE_NAME="${1#*=}"
            shift
            ;;
        --conda-env=*)
            CONDA_ENV="${1#*=}"
            shift
            ;;
        --build-env=*)
            BUILD_ENV="${1#*=}"
            shift
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Extract conda environment name from environment.yml
if [ -z "$CONDA_ENV" ] && [ -f "$CWD/environment.yml" ]; then
    CONDA_ENV=$(grep "^name:" "$CWD/environment.yml" | cut -d ":" -f2 | tr -d " ")
fi

# If not found in environment.yml, try .env file
if [ -z "$CONDA_ENV" ] && [ -f "$CWD/.env" ]; then
    CONDA_ENV=$(grep "^CONDA_ENV=" "$CWD/.env" | cut -d "=" -f2 | tr -d '"' | tr -d "'" | tr -d " ")
fi

# If still not found, throw an error
if [ -z "$CONDA_ENV" ]; then
    echo "Error: Conda environment name not found in environment.yml or .env"
    echo "Please specify with --conda-env option or add CONDA_ENV to .env file or name to environment.yml"
    exit 1
fi

# Set default paths if not provided
if [ -z "$SOURCE_DIR" ]; then
    SOURCE_DIR="../$PACKAGE_NAME"
fi

if [ -z "$DEST_DIR" ]; then
    DEST_DIR="./wheels"
fi

# Convert to absolute paths if relative
if [[ ! "$SOURCE_DIR" = /* ]]; then
    SOURCE_DIR="$CWD/$SOURCE_DIR"
fi

if [[ ! "$DEST_DIR" = /* ]]; then
    DEST_DIR="$CWD/$DEST_DIR"
fi

# Create wheels directory if it doesn't exist
mkdir -p "$DEST_DIR"

# Check for existing wheel in source directory
cd "$SOURCE_DIR" || { echo "Error: Could not change to source directory: $SOURCE_DIR"; exit 1; }
EXISTING_WHEEL=$(ls "dist/$PACKAGE_NAME-"*.whl 2>/dev/null)
if [ -n "$EXISTING_WHEEL" ] && [ "$FORCE_REPACKAGE" = false ]; then
    echo "Found existing wheel: $EXISTING_WHEEL"
    WHEEL_FILE="$EXISTING_WHEEL"
else
    if [ -n "$EXISTING_WHEEL" ]; then
        echo "Force repackage requested, rebuilding wheel..."
        rm -f "$EXISTING_WHEEL"
        echo "Removed existing wheel: $EXISTING_WHEEL"
    fi

    # Build wheel
    echo "Building $PACKAGE_NAME wheel in conda environment '$BUILD_ENV'..."
    conda run -n $BUILD_ENV python setup.py sdist bdist_wheel

    # Find the wheel file
    WHEEL_FILE=$(ls "dist/$PACKAGE_NAME-"*.whl 2>/dev/null)
    if [ -z "$WHEEL_FILE" ]; then
        echo "Error: No wheel file found in dist directory"
        exit 1
    fi
fi

# Get the wheel filename without path
WHEEL_FILENAME=$(basename "$WHEEL_FILE")

# Check if there's already a matching wheel file in the destination directory
LOCAL_WHEEL_FILE="$DEST_DIR/$WHEEL_FILENAME"
if [ -f "$LOCAL_WHEEL_FILE" ]; then
    # Calculate hashes for both files
    SOURCE_HASH=$(sha256sum "$WHEEL_FILE" | cut -d ' ' -f 1)
    LOCAL_HASH=$(sha256sum "$LOCAL_WHEEL_FILE" | cut -d ' ' -f 1)
    
    # Compare hashes
    if [ "$SOURCE_HASH" = "$LOCAL_HASH" ]; then
        if [ -z "$EXISTING_WHEEL" ] || [ "$FORCE_REPACKAGE" = true ]; then
            echo "Existing local $LOCAL_WHEEL_FILE already matches generated $WHEEL_FILE"
        else
            echo "Existing local $LOCAL_WHEEL_FILE already matches existing $WHEEL_FILE"
        fi
        echo "Skipping installation as files are identical."
        exit 0
    else
        echo "Local wheel exists but has different hash, will update..."
    fi
fi

# Copy wheel to destination directory
echo "Copying $(basename "$WHEEL_FILE") to wheels directory..."
cp "$WHEEL_FILE" "$DEST_DIR/"
WHEEL_FILE="$DEST_DIR/$(basename "$WHEEL_FILE")"

# Install new wheel
echo "Installing $(basename "$WHEEL_FILE") into conda environment '$CONDA_ENV'..."
conda run -n $CONDA_ENV pip install --force-reinstall "$WHEEL_FILE"

echo -e "\nSuccessfully installed $(basename "$WHEEL_FILE") into conda environment '$CONDA_ENV'" 
