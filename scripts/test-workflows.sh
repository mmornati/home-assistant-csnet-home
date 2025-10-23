#!/bin/bash

# Workflow Testing Script
# This script validates GitHub Actions workflows locally before pushing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    print_status "${BLUE}" "$1"
    echo "═══════════════════════════════════════════════════════════"
}

# Check if required tools are installed
check_dependencies() {
    print_header "Checking Dependencies"

    local missing_tools=()

    if ! command -v actionlint &> /dev/null; then
        missing_tools+=("actionlint")
    else
        print_status "${GREEN}" "✅ actionlint found: $(actionlint --version)"
    fi

    if ! command -v yamllint &> /dev/null; then
        missing_tools+=("yamllint")
    else
        print_status "${GREEN}" "✅ yamllint found: $(yamllint --version)"
    fi

    if ! command -v shellcheck &> /dev/null; then
        missing_tools+=("shellcheck")
    else
        print_status "${GREEN}" "✅ shellcheck found: $(shellcheck --version | head -2 | tail -1)"
    fi

    if ! command -v act &> /dev/null; then
        print_status "${YELLOW}" "⚠️  act not found (optional - for local workflow execution)"
    else
        print_status "${GREEN}" "✅ act found: $(act --version)"
    fi

    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_status "${RED}" "❌ Missing required tools: ${missing_tools[*]}"
        echo ""
        print_status "${YELLOW}" "Install missing tools:"
        for tool in "${missing_tools[@]}"; do
            case $tool in
                actionlint)
                    echo "  • actionlint: bash <(curl https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash)"
                    echo "    or: brew install actionlint (macOS)"
                    ;;
                yamllint)
                    echo "  • yamllint: pip install yamllint"
                    echo "    or: brew install yamllint (macOS)"
                    ;;
                shellcheck)
                    echo "  • shellcheck: brew install shellcheck (macOS)"
                    echo "    or: apt-get install shellcheck (Ubuntu)"
                    ;;
            esac
        done
        exit 1
    fi
}

# Run actionlint
run_actionlint() {
    print_header "Running ActionLint"

    if actionlint -color -verbose .github/workflows/*.yaml; then
        print_status "${GREEN}" "✅ ActionLint passed"
        return 0
    else
        print_status "${RED}" "❌ ActionLint failed"
        return 1
    fi
}

# Run yamllint
run_yamllint() {
    print_header "Running YAML Lint"

    if yamllint -d "{extends: default, rules: {line-length: {max: 120}, comments: {min-spaces-from-content: 1}}}" .github/workflows/; then
        print_status "${GREEN}" "✅ YAML Lint passed"
        return 0
    else
        print_status "${RED}" "❌ YAML Lint failed"
        return 1
    fi
}

# Run shellcheck
run_shellcheck() {
    print_header "Running ShellCheck"

    local shell_files=$(find .github scripts -type f -name "*.sh" 2>/dev/null)

    if [ -z "$shell_files" ]; then
        print_status "${YELLOW}" "⚠️  No shell scripts found"
        return 0
    fi

    local failed=0
    for file in $shell_files; do
        echo "Checking $file..."
        if ! shellcheck "$file"; then
            failed=1
        fi
    done

    if [ $failed -eq 0 ]; then
        print_status "${GREEN}" "✅ ShellCheck passed"
        return 0
    else
        print_status "${RED}" "❌ ShellCheck failed"
        return 1
    fi
}

# Validate workflow syntax
validate_syntax() {
    print_header "Validating Workflow Syntax"

    for workflow in .github/workflows/*.yaml; do
        echo "Validating $workflow..."
        if python3 -c "import yaml; yaml.safe_load(open('$workflow'))" 2>/dev/null; then
            print_status "${GREEN}" "  ✅ Valid YAML"
        else
            print_status "${RED}" "  ❌ Invalid YAML syntax"
            return 1
        fi
    done

    return 0
}

# Test zip creation locally
test_zip_creation() {
    print_header "Testing Zip Creation"

    cd custom_components/csnet_home || exit 1

    # Create test zip
    if zip -r test-hass-custom-csnet-home.zip . \
        -x "*.git*" \
        -x "*__pycache__*" \
        -x "*.pyc" \
        -x "*.pyo" \
        -x "*.DS_Store" \
        -x "*.pytest_cache*" \
        -x "*test-hass-custom-csnet-home.zip" > /dev/null 2>&1; then

        print_status "${GREEN}" "✅ Zip creation successful"
        print_status "${BLUE}" "   Size: $(ls -lh test-hass-custom-csnet-home.zip | awk '{print $5}')"
        print_status "${BLUE}" "   Files: $(zipinfo -t test-hass-custom-csnet-home.zip | grep 'files' | awk '{print $1}')"

        # Cleanup
        rm -f test-hass-custom-csnet-home.zip
        cd - > /dev/null
        return 0
    else
        print_status "${RED}" "❌ Zip creation failed"
        cd - > /dev/null
        return 1
    fi
}

# Main execution
main() {
    print_header "GitHub Actions Workflow Testing"
    print_status "${BLUE}" "Testing workflows in: $(pwd)"

    local exit_code=0

    check_dependencies

    validate_syntax || exit_code=1
    run_actionlint || exit_code=1
    run_yamllint || exit_code=1
    run_shellcheck || exit_code=1
    test_zip_creation || exit_code=1

    echo ""
    print_header "Summary"

    if [ $exit_code -eq 0 ]; then
        print_status "${GREEN}" "✅ All checks passed!"
        print_status "${GREEN}" "   Your workflows are ready to be pushed."
    else
        print_status "${RED}" "❌ Some checks failed."
        print_status "${YELLOW}" "   Please fix the issues before pushing."
    fi

    exit $exit_code
}

# Run main function
main "$@"
