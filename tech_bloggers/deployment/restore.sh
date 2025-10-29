#!/bin/bash
# Restore script for Tech-In-Bytes Django application
# Restores database and media files from a backup
#
# Usage: ./restore.sh <backup_file.tar.gz>

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No backup file specified${NC}"
    echo "Usage: $0 <backup_file.tar.gz>"
    echo ""
    echo "Available backups:"
    ls -lh /var/www/techinbytes/backups/*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

# Configuration
PROJECT_DIR="/var/www/techinbytes"
TEMP_DIR="/tmp/restore_$$"

# Database configuration (from .env)
source "$PROJECT_DIR/.env"

echo -e "${YELLOW}WARNING: This will restore data from backup and may overwrite existing data!${NC}"
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

echo -e "${GREEN}Starting restore process...${NC}"

# Create temporary directory
mkdir -p "$TEMP_DIR"

# Extract backup
echo "Extracting backup..."
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Find the backup directory (should be only one)
BACKUP_DIR=$(find "$TEMP_DIR" -type d -name "backup_*" | head -1)

if [ -z "$BACKUP_DIR" ]; then
    echo -e "${RED}Error: Invalid backup file structure${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Restore database
if [ -f "$BACKUP_DIR/database.dump" ]; then
    echo "Restoring database..."
    
    # Stop gunicorn to prevent database access during restore
    sudo systemctl stop gunicorn
    
    # Drop and recreate database (be careful!)
    echo "Dropping existing database..."
    PGPASSWORD="$DB_PASSWORD" dropdb \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        "$DB_NAME" 2>/dev/null || true
    
    echo "Creating new database..."
    PGPASSWORD="$DB_PASSWORD" createdb \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        "$DB_NAME"
    
    echo "Restoring database dump..."
    PGPASSWORD="$DB_PASSWORD" pg_restore \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        "$BACKUP_DIR/database.dump"
    
    echo -e "${GREEN}Database restored successfully${NC}"
else
    echo -e "${YELLOW}No database backup found in archive${NC}"
fi

# Restore media files
if [ -f "$BACKUP_DIR/media.tar.gz" ]; then
    echo "Restoring media files..."
    
    # Backup current media (just in case)
    if [ -d "$PROJECT_DIR/media" ]; then
        mv "$PROJECT_DIR/media" "$PROJECT_DIR/media.old.$$"
    fi
    
    # Extract media files
    tar -xzf "$BACKUP_DIR/media.tar.gz" -C "$PROJECT_DIR"
    
    # Set correct permissions
    chown -R django:www-data "$PROJECT_DIR/media"
    chmod -R 755 "$PROJECT_DIR/media"
    
    echo -e "${GREEN}Media files restored successfully${NC}"
else
    echo -e "${YELLOW}No media backup found in archive${NC}"
fi

# Clean up
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

# Start gunicorn
echo "Starting gunicorn..."
sudo systemctl start gunicorn

# Check if gunicorn started successfully
if sudo systemctl is-active --quiet gunicorn; then
    echo -e "${GREEN}Gunicorn started successfully${NC}"
else
    echo -e "${RED}Warning: Gunicorn failed to start${NC}"
    echo "Check logs: sudo journalctl -u gunicorn -n 50"
fi

echo ""
echo -e "${GREEN}Restore completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Verify the application is working correctly"
echo "2. If everything is okay, remove old media backup: rm -rf $PROJECT_DIR/media.old.$$"
echo "3. Check application logs: tail -f $PROJECT_DIR/logs/tech_bloggers.log"

