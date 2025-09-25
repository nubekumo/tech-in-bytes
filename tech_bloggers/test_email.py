#!/usr/bin/env python
"""
Test script to verify email configuration for password reset.
Run this from your project root: python test_email.py
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tech_bloggers.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email_configuration():
    """Test if email configuration is working."""
    print("🔍 Testing Email Configuration...")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print()
    
    # Test sending a simple email
    try:
        send_mail(
            subject='Test Email from Tech Bloggers',
            message='This is a test email to verify your email configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],  # This won't actually send
            fail_silently=False,
        )
        print("✅ Email configuration looks good!")
        
    except Exception as e:
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            print("✅ Console email backend is working - emails will print to console")
        else:
            print(f"❌ Email configuration error: {e}")
            print("\n💡 Try using the console backend for development:")
            print("EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend")

if __name__ == "__main__":
    test_email_configuration()

