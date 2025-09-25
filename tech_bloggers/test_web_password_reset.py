#!/usr/bin/env python
"""
Test password reset through Django's web interface simulation.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tech_bloggers.settings')
django.setup()

from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.conf import settings

User = get_user_model()

def test_password_reset_web():
    """Test password reset through web interface."""
    print("🌐 Testing Password Reset through Web Interface...")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print()
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='web_test_user',
        defaults={'email': 'web_test@example.com', 'is_active': True}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print('✅ Created test user: web_test_user')
    else:
        print('✅ Using existing test user: web_test_user')
    
    # Create test client
    client = Client()
    
    # Clear any existing emails
    mail.outbox = []
    
    print("📤 Submitting password reset form...")
    
    # Submit password reset form
    response = client.post('/accounts/password-reset/', {
        'email': 'web_test@example.com'
    })
    
    print(f"📊 Response status: {response.status_code}")
    print(f"📊 Response URL: {response.url}")
    
    if response.status_code == 302:
        print("✅ Form submitted successfully (redirected)")
        
        # Check if email was sent
        if hasattr(mail, 'outbox') and len(mail.outbox) > 0:
            email = mail.outbox[0]
            print("✅ Email found in mail.outbox!")
            print(f"📧 Subject: {email.subject}")
            print(f"📧 To: {email.to}")
            print(f"📧 Body length: {len(email.body)}")
        else:
            print("❌ No email found in mail.outbox")
            print("This might be because console backend doesn't populate mail.outbox")
    
    else:
        print(f"❌ Form submission failed: {response.status_code}")
        if hasattr(response, 'content'):
            print(f"Response content: {response.content.decode()[:200]}")

if __name__ == "__main__":
    test_password_reset_web()
