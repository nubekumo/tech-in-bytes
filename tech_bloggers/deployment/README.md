# Deployment Guide for Tech-In-Bytes

This directory contains all the necessary configuration files and scripts for deploying the Tech-In-Bytes Django application to AWS.

## Files Overview

### Configuration Files

- **`nginx.conf`** - Nginx web server configuration
  - Handles HTTPS/SSL termination
  - Proxies requests to Gunicorn
  - Serves static files (if not using S3)
  
- **`gunicorn.service`** - Systemd service file for Gunicorn
  - Manages the Gunicorn WSGI server as a system service
  - Handles automatic restarts and logging

### Scripts

- **`initial_setup.sh`** - One-time server setup script
  - Installs system dependencies
  - Creates users and directories
  - Configures firewall
  - Run once on a fresh server

- **`deploy.sh`** - Application deployment/update script
  - Pulls latest code
  - Installs dependencies
  - Runs migrations
  - Collects static files
  - Restarts services
  - Use for routine updates

- **`backup.sh`** - Database and media backup script
  - Creates compressed backups
  - Removes old backups based on retention policy
  - Optional S3 upload for off-site storage
  - Can be automated with cron

- **`restore.sh`** - Restore from backup script
  - Restores database and media files from a backup archive
  - Use in disaster recovery scenarios

## Deployment Process

### Initial Deployment

1. **Prepare Your Local Machine**
   ```bash
   # Copy env.example to .env and configure for production
   cp env.example .env
   # Edit .env with your production values
   ```

2. **Set Up AWS Infrastructure** (See main deployment plan)
   - Create RDS PostgreSQL database
   - Create S3 buckets for static/media files
   - Set up CloudFront distributions
   - Configure Route 53 DNS
   - Request ACM SSL certificate
   - Launch EC2 instance

3. **Initial Server Setup**
   ```bash
   # SSH into your EC2 instance
   ssh -i your-key.pem ubuntu@your-ec2-ip
   
   # Run initial setup script
   sudo bash initial_setup.sh
   ```

4. **Deploy Application**
   ```bash
   # Switch to django user
   sudo su - django
   
   # Navigate to project directory
   cd /var/www/techinbytes
   
   # Clone repository
   git clone <your-repo-url> .
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Create .env file with production settings
   nano .env  # Add all production environment variables
   
   # Run migrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   
   # Collect static files
   python manage.py collectstatic
   
   # If using database cache
   python manage.py createcachetable
   ```

5. **Configure Nginx**
   ```bash
   # Exit django user
   exit
   
   # Copy nginx config
   sudo cp /var/www/techinbytes/deployment/nginx.conf /etc/nginx/sites-available/techinbytes
   
   # Edit with your domain
   sudo nano /etc/nginx/sites-available/techinbytes
   
   # Enable site
   sudo ln -s /etc/nginx/sites-available/techinbytes /etc/nginx/sites-enabled/
   
   # Test configuration
   sudo nginx -t
   
   # Restart Nginx
   sudo systemctl restart nginx
   ```

6. **Configure Gunicorn Service**
   ```bash
   # Copy service file
   sudo cp /var/www/techinbytes/deployment/gunicorn.service /etc/systemd/system/
   
   # Reload systemd
   sudo systemctl daemon-reload
   
   # Enable and start service
   sudo systemctl enable gunicorn
   sudo systemctl start gunicorn
   
   # Check status
   sudo systemctl status gunicorn
   ```

7. **Get SSL Certificate**
   ```bash
   # Using Let's Encrypt Certbot
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   
   # Test auto-renewal
   sudo certbot renew --dry-run
   ```

### Routine Updates

For application updates (code changes, dependency updates):

```bash
# SSH into server
ssh -i your-key.pem ubuntu@your-ec2-ip

# Switch to django user
sudo su - django

# Navigate to project directory
cd /var/www/techinbytes

# Run deployment script
./deployment/deploy.sh
```

**Deploy script options:**
- `--no-migrate` - Skip database migrations
- `--no-static` - Skip static file collection
- `--no-restart` - Skip service restart

### Backups

**Manual Backup:**
```bash
cd /var/www/techinbytes
./deployment/backup.sh
```

**Automated Backups (Cron):**
```bash
# Edit crontab
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /var/www/techinbytes/deployment/backup.sh >> /var/www/techinbytes/logs/backup.log 2>&1
```

**Restore from Backup:**
```bash
cd /var/www/techinbytes
./deployment/restore.sh /var/www/techinbytes/backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

## Troubleshooting

### Check Service Status
```bash
# Gunicorn
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -f

# Nginx
sudo systemctl status nginx
sudo nginx -t

# Application logs
tail -f /var/www/techinbytes/logs/tech_bloggers.log
tail -f /var/www/techinbytes/logs/error.log
```

### Common Issues

1. **Gunicorn won't start**
   - Check permissions on socket file
   - Check .env file has correct values
   - Check virtual environment is activated
   - View logs: `sudo journalctl -u gunicorn -n 50`

2. **502 Bad Gateway**
   - Gunicorn is not running
   - Socket path mismatch between nginx and gunicorn
   - Permissions issue on socket file

3. **Static files not loading**
   - Run `python manage.py collectstatic`
   - Check S3 bucket permissions
   - Verify CloudFront distribution is working
   - Check STATIC_URL in settings

4. **Database connection issues**
   - Verify RDS security group allows EC2 access
   - Check database credentials in .env
   - Test connection: `psql -h HOST -U USER -d DBNAME`

5. **Email not sending**
   - Check SES/SMTP credentials
   - Verify SES is out of sandbox mode
   - Check security group allows outbound port 587

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated and set
- [ ] Database password is strong and secure
- [ ] AWS credentials stored securely (not in code)
- [ ] Firewall (UFW) configured properly
- [ ] SSH key authentication only (no password login)
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`
- [ ] SSL certificate installed and auto-renewal working
- [ ] Security headers configured in Nginx
- [ ] File permissions set correctly (755 for directories, 644 for files)
- [ ] Sensitive files (.env, *.pem) not accessible via web

## Monitoring

### Log Locations
- Application: `/var/www/techinbytes/logs/tech_bloggers.log`
- Errors: `/var/www/techinbytes/logs/error.log`
- Gunicorn: `/var/www/techinbytes/logs/gunicorn-*.log`
- Nginx: `/var/log/nginx/techinbytes-*.log`
- System: `sudo journalctl -u gunicorn`

### Health Checks
```bash
# Check if site is responding
curl -I https://yourdomain.com

# Check SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check disk space
df -h

# Check memory usage
free -m

# Check running processes
ps aux | grep gunicorn
```

## Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)

