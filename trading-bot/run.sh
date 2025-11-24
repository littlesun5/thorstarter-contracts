#!/bin/bash
#
# Trading Bot Runner Script
# Provides easy commands to manage the trading bot
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Trading Bot Manager"
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Install dependencies and configure environment"
    echo "  test      - Test connection to Backpack Exchange"
    echo "  start     - Start the trading bot"
    echo "  monitor   - Start the monitoring dashboard"
    echo "  stop      - Stop all bot processes"
    echo "  logs      - View bot logs"
    echo "  help      - Show this help message"
    echo ""
}

# Check if Python 3 is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        exit 1
    fi
}

# Setup function
setup() {
    echo -e "${GREEN}Setting up Trading Bot...${NC}"
    check_python
    python3 setup.py
}

# Test connection function
test_connection() {
    echo -e "${GREEN}Testing connection to Backpack Exchange...${NC}"
    check_python
    cd src && python3 test_connection.py
}

# Start bot function
start_bot() {
    echo -e "${GREEN}Starting Trading Bot...${NC}"
    check_python
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        echo -e "${RED}Error: .env file not found${NC}"
        echo "Please run './run.sh setup' first"
        exit 1
    fi
    
    # Start the bot
    cd src && python3 trading_bot.py
}

# Start monitor function
start_monitor() {
    echo -e "${GREEN}Starting Monitor Dashboard...${NC}"
    check_python
    cd src && python3 monitor.py
}

# Stop all processes
stop_all() {
    echo -e "${YELLOW}Stopping all bot processes...${NC}"
    
    # Kill Python processes running our scripts
    pkill -f "trading_bot.py"
    pkill -f "monitor.py"
    
    echo -e "${GREEN}All processes stopped${NC}"
}

# View logs
view_logs() {
    if [ -d "logs" ]; then
        echo -e "${GREEN}Recent log files:${NC}"
        ls -la logs/
        
        # If there are log files, show the latest
        if [ "$(ls -A logs/)" ]; then
            latest_log=$(ls -t logs/*.log 2>/dev/null | head -1)
            if [ -n "$latest_log" ]; then
                echo ""
                echo -e "${GREEN}Showing last 50 lines of $latest_log:${NC}"
                tail -50 "$latest_log"
            fi
        else
            echo "No log files found"
        fi
    else
        echo "Logs directory does not exist"
    fi
}

# Main script logic
case "$1" in
    setup)
        setup
        ;;
    test)
        test_connection
        ;;
    start)
        start_bot
        ;;
    monitor)
        start_monitor
        ;;
    stop)
        stop_all
        ;;
    logs)
        view_logs
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        usage
        exit 1
        ;;
esac