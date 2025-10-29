#!/bin/bash
# Deployment script for Tech-In-Bytes Django application
# This script handles application updates on the production server
#
# Usage: ./deploy.sh [--no-migrate] [--no-static] [--no-restart]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/techinbytes"
VENV_DIR="$PROJECT_DIR/venv"
MANAGE_PY="$PROJECT_DIR/manage.py"

# Parse arguments
SKIP_MIGRATE=false
SKIP_STATIC=false
SKIP_RESTART=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-migrate)
            SKIP_MIGRATE=true
            shift
            ;;
        --no-static)
            SKIP_STATIC=true
            shift
            ;;
        --no-restart)
            SKIP_RESTART=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}Starting deployment...${NC}"

# Navigate to project directory
cd "$PROJECT_DIR"

# Pull latest code from repository
echo -e "${YELLOW}Pulling latest code...${NC}"
git pull origin main

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Install/update dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt --quiet

# Run database migrations
if [ "$SKIP_MIGRATE" = false ]; then
    echo -e "${YELLOW}Running database migrations...${NC}"
    python "$MANAGE_PY" migrate --noinput
else
    echo -e "${YELLOW}Skipping migrations (--no-migrate flag)${NC}"
fi

# Collect static files
if [ "$SKIP_STATIC" = false ]; then
    echo -e "${YELLOW}Collecting static files...${NC}"
    python "$MANAGE_PY" collectstatic --noinput --clear
else
    echo -e "${YELLOW}Skipping static collection (--no-static flag)${NC}"
fi

# Create cache table if using database cache (only needs to be done once)
# Uncomment if using database cache in production
# python "$MANAGE_PY" createcachetable

# Restart Gunicorn
if [ "$SKIP_RESTART" = false ]; then
    echo -e "${YELLOW}Restarting Gunicorn...${NC}"
    sudo systemctl restart gunicorn
    
    # Check if restart was successful
    if sudo systemctl is-active --quiet gunicorn; then
        echo -e "${GREEN}Gunicorn restarted successfully${NC}"
    else
        echo -e "${RED}Gunicorn failed to restart!${NC}"
        echo "Check logs: sudo journalctl -u gunicorn -n 50"
        exit 1
    fi
else
    echo -e "${YELLOW}Skipping Gunicorn restart (--no-restart flag)${NC}"
fi

# Clear Django cache (optional)
# python "$MANAGE_PY" clear_cache

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo ""
echo "Useful commands:"
echo "  - Check Gunicorn status: sudo systemctl status gunicorn"
echo "  - View Gunicorn logs: sudo journalctl -u gunicorn -f"
echo "  - View application logs: tail -f $PROJECT_DIR/logs/tech_bloggers.log"
echo "  - Test Nginx config: sudo nginx -t"
echo "  - Reload Nginx: sudo systemctl reload nginx"

