#!/usr/bin/env python
"""
Debug script for password reset email issue.
Run this to test if password reset emails are working.
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

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings

User = get_user_model()

def test_password_reset_email():
    """Test password reset email functionality."""
    print("🔍 Testing Password Reset Email...")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"DEBUG: {settings.DEBUG}")
    print()
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='debug_user',
        defaults={'email': 'debug@example.com', 'is_active': True}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print('✅ Created test user: debug_user')
    else:
        print('✅ Using existing test user: debug_user')
    
    # Generate password reset token
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    # Create context
    context = {
        'user': user,
        'protocol': 'http',
        'domain': '127.0.0.1:8000',
        'uid': uid,
        'token': token,
    }
    
    # Render email content
    subject = render_to_string('accounts/password_reset_subject.txt', context).strip()
    email_html = render_to_string('accounts/password_reset_email.html', context)
    
    print(f"📧 Subject: {subject}")
    print(f"📧 Email length: {len(email_html)} characters")
    print()
    
    # Send email
    print("📤 Sending password reset email...")
    try:
        send_mail(
            subject=subject,
            message=email_html,
            from_email=None,
            recipient_list=[user.email],
            html_message=email_html,
        )
        print("✅ Password reset email sent successfully!")
        print("📋 Check the output above for the email content.")
        print()
        print("🔗 Reset link:")
        print(f"http://127.0.0.1:8000/accounts/password-reset/{uid}/{token}/")
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_password_reset_email()
