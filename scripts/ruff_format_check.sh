#!/bin/bash

# Script to run ruff format and ruff check
# Usage: ./scripts/ruff_format_check.sh

set -e

echo "Running ruff format..."
ruff format

echo "Running ruff check..."
ruff check

echo "Finished formatting and checking code." 