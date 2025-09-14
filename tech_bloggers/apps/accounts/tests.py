from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from .models import Profile
from .forms import SignUpForm, AccountSettingsForm, CustomPasswordChangeForm

class BaseTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()
        # Create associated profile
        self.profile = Profile.objects.create(user=self.user)

    def login(self):
        """Helper method to login the test user"""
        self.client.login(username='testuser', password='testpass123')

class SignUpTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('accounts:signup')
        self.signup_done_url = reverse('accounts:signup_done')

    def test_signup_page_loads(self):
        """Test that signup page loads correctly"""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/signup.html')
        self.assertIsInstance(response.context['form'], SignUpForm)

    def test_signup_with_valid_data(self):
        """Test user registration with valid data"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        response = self.client.post(self.signup_url, data)
        
        # Check redirect to signup done page
        self.assertRedirects(response, self.signup_done_url)
        
        # Check user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        
        # Check user is inactive (awaiting email activation)
        self.assertFalse(user.is_active)
        
        # Check profile was created
        self.assertTrue(Profile.objects.filter(user=user).exists())
        
        # Check activation email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Activate your Tech Bloggers account')
        self.assertEqual(mail.outbox[0].to, ['newuser@example.com'])

    def test_signup_with_invalid_data(self):
        """Test user registration with invalid data"""
        # Test with missing fields
        response = self.client.post(self.signup_url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

        # Test with mismatched passwords
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'wrongpass123'
        }
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(User.objects.filter(username='newuser').exists())

class AccountActivationTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an inactive user
        self.user = User.objects.create_user(
            username='inactiveuser',
            email='inactive@example.com',
            password='testpass123'
        )
        self.user.is_active = False
        self.user.save()
        Profile.objects.create(user=self.user)

        # Generate activation token
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

    def test_account_activation_success(self):
        """Test successful account activation"""
        url = reverse('accounts:activate', kwargs={'uidb64': self.uid, 'token': self.token})
        response = self.client.get(url)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('pages:index'))
        
        # Refresh user from database
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_account_activation_invalid_token(self):
        """Test account activation with invalid token"""
        url = reverse('accounts:activate', kwargs={'uidb64': self.uid, 'token': 'invalid-token'})
        response = self.client.get(url)
        
        # Check redirect to activation failed page
        self.assertRedirects(response, reverse('accounts:activation_failed'))
        
        # User should still be inactive
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

class LoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        # Create an active user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()
        Profile.objects.create(user=self.user)

    def test_login_page_loads(self):
        """Test that login page loads correctly"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_login_with_valid_credentials(self):
        """Test login with valid credentials"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('pages:index'))
        
        # Check user is logged in
        user = response.wsgi_request.user
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.username, 'testuser')

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Test with wrong password
        data = {
            'username': 'testuser',
            'password': 'wrongpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Test with non-existent user
        data = {
            'username': 'nonexistentuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_with_inactive_user(self):
        """Test login with inactive user account"""
        # Make user inactive
        self.user.is_active = False
        self.user.save()
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_redirects_authenticated_user(self):
        """Test that authenticated users are redirected from login page"""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Try to access login page
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('pages:index'))

class LogoutTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('accounts:logout')
        # Create and login a user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_logout_success(self):
        """Test successful logout"""
        response = self.client.post(self.logout_url)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('pages:index'))
        
        # Check user is logged out
        self.assertFalse(response.wsgi_request.user.is_authenticated)

class PasswordChangeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.settings_url = reverse('accounts:settings')
        self.password_change_url = reverse('accounts:update_password')
        # Create and login a user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_password_change_page_loads(self):
        """Test that password change form loads correctly in settings page"""
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/settings.html')
        self.assertIsInstance(response.context['password_form'], CustomPasswordChangeForm)

    def test_password_change_success(self):
        """Test successful password change"""
        data = {
            'old_password': 'testpass123',
            'new_password1': 'newtestpass123',
            'new_password2': 'newtestpass123'
        }
        response = self.client.post(self.password_change_url, data)
        
        # Check redirect to settings page
        self.assertRedirects(response, self.settings_url)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newtestpass123'))
        
        # Verify user is still logged in
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_password_change_invalid_old_password(self):
        """Test password change with wrong old password"""
        data = {
            'old_password': 'wrongpass123',
            'new_password1': 'newtestpass123',
            'new_password2': 'newtestpass123'
        }
        response = self.client.post(self.password_change_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/settings.html')
        
        # Verify password was not changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('testpass123'))

    def test_password_change_password_mismatch(self):
        """Test password change with mismatched new passwords"""
        data = {
            'old_password': 'testpass123',
            'new_password1': 'newtestpass123',
            'new_password2': 'differentpass123'
        }
        response = self.client.post(self.password_change_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/settings.html')
        
        # Verify password was not changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('testpass123'))

    def test_password_change_requires_login(self):
        """Test that password change requires authentication"""
        # Logout first
        self.client.logout()
        
        data = {
            'old_password': 'testpass123',
            'new_password1': 'newtestpass123',
            'new_password2': 'newtestpass123'
        }
        response = self.client.post(self.password_change_url, data)
        
        # Should redirect to login page
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.password_change_url}")
        
        # Verify password was not changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('testpass123'))

class ProfileSettingsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.settings_url = reverse('accounts:settings')
        self.profile_settings_url = reverse('accounts:update_profile')
        # Create and login a user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_settings_page_loads(self):
        """Test that settings page loads correctly"""
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/settings.html')
        self.assertIsInstance(response.context['settings_form'], AccountSettingsForm)
        self.assertIsInstance(response.context['password_form'], CustomPasswordChangeForm)

    def test_settings_page_requires_login(self):
        """Test that settings page requires authentication"""
        self.client.logout()
        response = self.client.get(self.settings_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.settings_url}")

    def test_update_email_success(self):
        """Test successful email update"""
        data = {
            'email': 'newemail@example.com',
            'avatar': ''  # No avatar update
        }
        response = self.client.post(self.profile_settings_url, data)
        
        # Check redirect to settings page
        self.assertRedirects(response, self.settings_url)
        
        # Verify email was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')

    def test_update_avatar_success(self):
        """Test successful avatar update"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.conf import settings
        import os
        
        # Create a test image file
        image_path = os.path.join(settings.MEDIA_ROOT, 'post_images', 'mountains.jpg')
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        avatar = SimpleUploadedFile('test_avatar.jpg', image_data, content_type='image/jpeg')
        data = {
            'email': 'testuser@example.com',  # Keep same email
            'avatar': avatar
        }
        response = self.client.post(self.profile_settings_url, data)
        
        # Check redirect to settings page
        self.assertRedirects(response, self.settings_url)
        
        # Verify avatar was updated
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.avatar)
        self.assertTrue(os.path.exists(self.profile.avatar.path))

    def test_update_invalid_email(self):
        """Test profile update with invalid email"""
        data = {
            'email': 'invalid-email',
            'avatar': ''
        }
        response = self.client.post(self.profile_settings_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/settings.html')
        
        # Verify email was not updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'testuser@example.com')

class AccountDeletionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.delete_url = reverse('accounts:delete_account')
        # Create and login a user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_delete_confirmation_page_loads(self):
        """Test that delete confirmation page loads correctly"""
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/delete_confirm.html')

    def test_delete_confirmation_requires_login(self):
        """Test that delete confirmation page requires authentication"""
        self.client.logout()
        response = self.client.get(self.delete_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.delete_url}")

    def test_account_deletion_success(self):
        """Test successful account deletion"""
        response = self.client.post(self.delete_url)
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('pages:index'))
        
        # Verify user and profile were deleted
        self.assertFalse(User.objects.filter(username='testuser').exists())
        self.assertFalse(Profile.objects.filter(user=self.user).exists())
        
        # Verify user is logged out
        response = self.client.get(reverse('accounts:settings'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:settings')}")

    def test_account_deletion_requires_login(self):
        """Test that account deletion requires authentication"""
        self.client.logout()
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.delete_url}")
        
        # Verify user and profile still exist
        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertTrue(Profile.objects.filter(user=self.user).exists())