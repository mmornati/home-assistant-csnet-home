#!/bin/bash

# Integration Testing Script for CSNet Home Custom Component
# This script provides easy commands to test the integration locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

print_header() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}\n"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

show_help() {
    cat << EOF
Usage: $0 [COMMAND]

Integration Testing for CSNet Home Custom Component
This script tests your LOCAL development code (custom_components/csnet_home/)
NOT a downloaded or released version.

Commands:
    start       Start Home Assistant with YOUR LOCAL CODE mounted
    stop        Stop the Home Assistant test instance
    restart     Restart to apply code changes
    logs        Show logs from Home Assistant (follow mode)
    logs-tail   Show last 100 lines of logs
    status      Check if Home Assistant is running and verify mounted code
    clean       Remove all test data (including database and config)
    open        Open Home Assistant in your default browser
    test        Run unit tests before starting integration test
    help        Show this help message

Examples:
    $0 start        # Start Home Assistant with your local code
    $0 logs         # Watch the logs in real-time
    $0 restart      # Restart after making code changes
    $0 status       # Check status and verify local code is mounted
    $0 stop         # Stop when done testing
    $0 clean        # Clean up all test data and start fresh

Development Workflow:
    1. $0 start              # Start testing environment
    2. Edit your code in custom_components/csnet_home/
    3. $0 restart            # Apply your changes
    4. Test in browser at http://localhost:8123
    5. $0 logs               # Check for errors
    6. Repeat steps 2-5 as needed
    7. $0 stop               # Stop when done

EOF
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker compose version &> /dev/null && ! docker-compose --version &> /dev/null; then
        print_error "Docker Compose is not installed"
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

verify_local_code() {
    print_info "Verifying local development code..."

    if [ ! -d "$PROJECT_DIR/custom_components/csnet_home" ]; then
        print_error "Local custom component not found at: $PROJECT_DIR/custom_components/csnet_home"
        return 1
    fi

    # Show what version/files we're testing
    local manifest="$PROJECT_DIR/custom_components/csnet_home/manifest.json"
    if [ -f "$manifest" ]; then
        local version=$(grep -o '"version": "[^"]*"' "$manifest" | cut -d'"' -f4)
        print_success "Testing LOCAL development code (version: $version)"
    else
        print_success "Testing LOCAL development code"
    fi

    # List main files to confirm what's being tested
    echo ""
    print_info "Files being tested from: custom_components/csnet_home/"
    ls -1 "$PROJECT_DIR/custom_components/csnet_home/"*.py 2>/dev/null | xargs -n1 basename | sed 's/^/  - /'
    echo ""

    return 0
}

start_homeassistant() {
    print_header "Starting Home Assistant for Integration Testing"

    check_docker

    # Verify local code exists and show what we're testing
    verify_local_code || exit 1

    print_info "Building and starting Home Assistant container..."
    print_info "This will mount your LOCAL code from: custom_components/csnet_home/"
    echo ""
    docker compose up -d

    print_success "Home Assistant is starting!"
    echo ""
    print_info "The first start may take 2-3 minutes..."
    print_info "Home Assistant will be available at: http://localhost:8123"
    echo ""
    print_info "Waiting for Home Assistant to be ready..."

    # Wait for Home Assistant to be ready
    local max_attempts=60
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8123 > /dev/null 2>&1; then
            print_success "Home Assistant is ready!"
            echo ""

            # Verify the local code is mounted
            if docker exec home-assistant-csnet-test test -f /config/custom_components/csnet_home/manifest.json 2>/dev/null; then
                print_success "✓ Local development code is properly mounted!"
            else
                print_error "⚠ Warning: Local code may not be mounted correctly"
            fi

            echo ""
            print_info "You can now:"
            echo "  1. Open http://localhost:8123 in your browser"
            echo "  2. Create an admin account (first time only)"
            echo "  3. Go to Configuration → Integrations"
            echo "  4. Click 'Add Integration' and search for 'Hitachi CSNet Home'"
            echo "  5. Configure the integration with your credentials"
            echo ""
            echo -e "${YELLOW}📝 Important: After making code changes, run:${NC}"
            echo -e "   ${GREEN}$0 restart${NC}  or  ${GREEN}make restart${NC}"
            echo ""
            print_info "To view logs, run: $0 logs"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
        echo -n "."
    done

    echo ""
    print_error "Home Assistant did not start in time. Check logs with: $0 logs"
    return 1
}

stop_homeassistant() {
    print_header "Stopping Home Assistant"

    check_docker
    docker compose down

    print_success "Home Assistant stopped"
}

restart_homeassistant() {
    print_header "Restarting Home Assistant"

    stop_homeassistant
    sleep 2
    start_homeassistant
}

show_logs() {
    print_header "Home Assistant Logs (Ctrl+C to exit)"

    check_docker
    docker compose logs -f
}

show_logs_tail() {
    print_header "Last 100 lines of Home Assistant Logs"

    check_docker
    docker compose logs --tail=100
}

check_status() {
    print_header "Home Assistant Status"

    check_docker

    if docker compose ps | grep -q "home-assistant-csnet-test.*Up"; then
        print_success "Home Assistant is running"
        echo ""
        docker compose ps
        echo ""
        print_info "Access Home Assistant at: http://localhost:8123"

        # Check if it's responding
        if curl -s http://localhost:8123 > /dev/null 2>&1; then
            print_success "Home Assistant is responding"
        else
            print_error "Home Assistant is running but not responding yet"
            print_info "It may still be starting up. Check logs with: $0 logs"
        fi

        echo ""
        print_info "Checking mounted code..."

        # Verify local code is mounted
        if docker exec home-assistant-csnet-test test -f /config/custom_components/csnet_home/manifest.json 2>/dev/null; then
            local version=$(docker exec home-assistant-csnet-test cat /config/custom_components/csnet_home/manifest.json 2>/dev/null | grep -o '"version": "[^"]*"' | cut -d'"' -f4)
            print_success "✓ Local development code is mounted (version: $version)"
            print_info "Location: custom_components/csnet_home/"
            echo ""
            print_info "After making code changes, restart with: $0 restart"
        else
            print_error "⚠ Warning: Local code may not be mounted correctly"
        fi
    else
        print_error "Home Assistant is not running"
        print_info "Start it with: $0 start"
    fi
}

clean_data() {
    print_header "Cleaning Test Data"

    # Stop Home Assistant first
    if docker compose ps | grep -q "home-assistant-csnet-test"; then
        print_info "Stopping Home Assistant..."
        docker compose down
    fi

    print_info "Removing Docker volumes..."
    docker compose down -v

    print_info "Removing test configuration data..."
    if [ -d "$PROJECT_DIR/test_config/.storage" ]; then
        rm -rf "$PROJECT_DIR/test_config/.storage"
    fi

    # Remove database files
    rm -f "$PROJECT_DIR/test_config/"*.db*
    rm -f "$PROJECT_DIR/test_config/"*.log*

    print_success "Test data cleaned"
    print_info "You can now start fresh with: $0 start"
}

open_browser() {
    print_info "Opening Home Assistant in browser..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open http://localhost:8123
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open http://localhost:8123 2>/dev/null || echo "Please open http://localhost:8123 in your browser"
    else
        print_info "Please open http://localhost:8123 in your browser"
    fi
}

run_unit_tests() {
    print_header "Running Unit Tests"

    if [ -d "$PROJECT_DIR/venv" ]; then
        print_info "Using existing virtual environment..."
        source "$PROJECT_DIR/venv/bin/activate"
    else
        print_error "Virtual environment not found"
        print_info "Please create a virtual environment and install dependencies first"
        return 1
    fi

    print_info "Running pytest..."
    pytest tests/ -v

    if [ $? -eq 0 ]; then
        print_success "All unit tests passed!"
        return 0
    else
        print_error "Some tests failed"
        return 1
    fi
}

# Main script logic
case "${1:-help}" in
    start)
        start_homeassistant
        ;;
    stop)
        stop_homeassistant
        ;;
    restart)
        restart_homeassistant
        ;;
    logs)
        show_logs
        ;;
    logs-tail)
        show_logs_tail
        ;;
    status)
        check_status
        ;;
    clean)
        clean_data
        ;;
    open)
        open_browser
        ;;
    test)
        run_unit_tests
        if [ $? -eq 0 ]; then
            echo ""
            print_info "Unit tests passed! You can now start integration testing."
            print_info "Run: $0 start"
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
