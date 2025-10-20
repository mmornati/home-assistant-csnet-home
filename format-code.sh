#!/bin/bash

# Script to format code before committing
# This prevents the need to manually stage changes after pre-commit runs

echo "Formatting code with Black..."
black .

echo "Running other pre-commit hooks..."
pre-commit run --all-files

echo "Staging any changes made by formatters..."
git add -A

echo "Code formatting complete. You can now commit normally."
