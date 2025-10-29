#!/bin/bash
# Backup script for Tech-In-Bytes Django application
# Creates backups of database and media files
#
# Usage: ./backup.sh
# 
# For automated backups, add to crontab:
# 0 2 * * * /var/www/techinbytes/deployment/backup.sh >> /var/www/techinbytes/logs/backup.log 2>&1

set -e  # Exit on error

# Configuration
PROJECT_DIR="/var/www/techinbytes"
BACKUP_DIR="$PROJECT_DIR/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_$DATE"

# Database configuration (from .env)
source "$PROJECT_DIR/.env"

# Retention (days)
RETENTION_DAYS=30

echo "Starting backup at $(date)"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create temporary backup directory
TEMP_BACKUP="$BACKUP_DIR/$BACKUP_NAME"
mkdir -p "$TEMP_BACKUP"

# Backup database (PostgreSQL)
echo "Backing up database..."
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -F c \
    -f "$TEMP_BACKUP/database.dump"

# Backup media files (if not using S3 exclusively)
if [ "$USE_S3_MEDIA" != "True" ]; then
    echo "Backing up media files..."
    if [ -d "$PROJECT_DIR/media" ]; then
        tar -czf "$TEMP_BACKUP/media.tar.gz" -C "$PROJECT_DIR" media
    fi
fi

# Backup .env file (optional, be careful with sensitive data)
echo "Backing up configuration..."
cp "$PROJECT_DIR/.env" "$TEMP_BACKUP/env.backup"

# Create final compressed archive
echo "Creating compressed archive..."
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$TEMP_BACKUP"

# Calculate backup size
BACKUP_SIZE=$(du -h "$BACKUP_NAME.tar.gz" | cut -f1)
echo "Backup created: $BACKUP_NAME.tar.gz (Size: $BACKUP_SIZE)"

# Remove old backups
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
echo "Old backups removed"

# Optional: Upload to S3 for off-site backup
if [ "$BACKUP_TO_S3" = "True" ] && [ ! -z "$BACKUP_S3_BUCKET" ]; then
    echo "Uploading backup to S3..."
    aws s3 cp "$BACKUP_DIR/$BACKUP_NAME.tar.gz" "s3://$BACKUP_S3_BUCKET/backups/"
    echo "Backup uploaded to S3"
fi

echo "Backup completed successfully at $(date)"
echo "Backup location: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
echo ""

# Show available backups
echo "Available backups:"
ls -lh "$BACKUP_DIR"/*.tar.gz | tail -5

