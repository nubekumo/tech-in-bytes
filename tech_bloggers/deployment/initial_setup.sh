#!/bin/bash
# Initial server setup script for Tech-In-Bytes Django application
# Run this script once on a fresh server to set up the environment
#
# Usage: sudo bash initial_setup.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}Starting initial server setup...${NC}"

# Update system packages
echo -e "${YELLOW}Updating system packages...${NC}"
apt update
apt upgrade -y

# Install required packages
echo -e "${YELLOW}Installing required packages...${NC}"
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    nginx \
    postgresql-client \
    git \
    build-essential \
    libpq-dev \
    ufw

# Create django user if it doesn't exist
if ! id "django" &>/dev/null; then
    echo -e "${YELLOW}Creating django user...${NC}"
    useradd -m -s /bin/bash django
    usermod -aG www-data django
    echo -e "${GREEN}User 'django' created${NC}"
else
    echo -e "${YELLOW}User 'django' already exists${NC}"
fi

# Create project directory
echo -e "${YELLOW}Creating project directory...${NC}"
mkdir -p /var/www/techinbytes
chown django:www-data /var/www/techinbytes
chmod 755 /var/www/techinbytes

# Create logs directory
mkdir -p /var/www/techinbytes/logs
chown django:www-data /var/www/techinbytes/logs
chmod 755 /var/www/techinbytes/logs

# Configure firewall (UFW)
echo -e "${YELLOW}Configuring firewall...${NC}"
ufw --force enable
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP (CloudFront will connect here)
# Note: No need to open 443 - CloudFront handles HTTPS
ufw status

echo -e "${GREEN}Initial server setup completed!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Switch to django user: sudo su - django"
echo "2. Navigate to project directory: cd /var/www/techinbytes"
echo "3. Clone your repository: git clone <your-repo-url> ."
echo "4. Create virtual environment: python3 -m venv venv"
echo "5. Activate venv: source venv/bin/activate"
echo "6. Install dependencies: pip install -r requirements.txt"
echo "7. Create .env file with production environment variables"
echo "8. Run migrations: python manage.py migrate"
echo "9. Create superuser: python manage.py createsuperuser"
echo "10. Collect static files: python manage.py collectstatic"
echo "11. Copy and configure nginx config: sudo cp deployment/nginx.conf /etc/nginx/sites-available/techinbytes"
echo "12. Enable nginx site: sudo ln -s /etc/nginx/sites-available/techinbytes /etc/nginx/sites-enabled/"
echo "13. Copy and enable gunicorn service: sudo cp deployment/gunicorn.service /etc/systemd/system/"
echo "14. Reload systemd: sudo systemctl daemon-reload"
echo "15. Enable and start gunicorn: sudo systemctl enable --now gunicorn"
echo "16. Test nginx config: sudo nginx -t"
echo "17. Restart nginx: sudo systemctl restart nginx"
echo "18. Configure CloudFront distribution to point to your EC2 instance"
echo "19. Associate your ACM certificate with CloudFront"

