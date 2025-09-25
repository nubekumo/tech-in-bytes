from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from PIL import Image
import os
import io
from .models import Profile
from .forms import (
    SignUpForm, AccountSettingsForm, CustomPasswordChangeForm, 
    EmailUpdateForm, CustomAuthenticationForm
)
from .views import account_activation_token
from .utils import process_avatar_image

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
        self.token = account_activation_token.make_token(self.user)

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

    def test_login_allows_authenticated_user(self):
        """Test that authenticated users can still access login page"""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Try to access login page
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

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


class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='resetuser',
            email='resetuser@example.com',
            password='OldPassw0rd!',
            is_active=True,
        )

    def test_password_reset_page_renders(self):
        url = reverse('accounts:password_reset')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Reset Your Password')

    def test_password_reset_post_unknown_email_shows_inline_message(self):
        url = reverse('accounts:password_reset')
        resp = self.client.post(url, {'email': 'doesnotexist@example.com'})
        # Custom view keeps user on the same page with inline message
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Please check the email address and try again.')
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_sends_email_and_redirects(self):
        url = reverse('accounts:password_reset')
        resp = self.client.post(url, {'email': self.user.email})
        self.assertRedirects(resp, reverse('accounts:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password Reset Request', mail.outbox[0].subject)

    def test_password_reset_confirm_sets_new_password(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        confirm_url = reverse('accounts:password_reset_confirm', args=[uidb64, token])

        # Load confirm page (may redirect to '/set-password/') and capture final URL
        resp_get = self.client.get(confirm_url, follow=True)
        self.assertEqual(resp_get.status_code, 200)
        set_password_url = resp_get.request.get('PATH_INFO', confirm_url)

        # Submit new password to the final set-password URL
        resp_post = self.client.post(set_password_url, {
            'new_password1': 'NewPassw0rd!',
            'new_password2': 'NewPassw0rd!'
        })
        self.assertRedirects(resp_post, reverse('accounts:password_reset_complete'))

        # Can login with new password
        logged_in = self.client.login(username='resetuser', password='NewPassw0rd!')
        self.assertTrue(logged_in)

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
        self.assertIsInstance(response.context['form'], AccountSettingsForm)
        self.assertIsInstance(response.context['password_form'], CustomPasswordChangeForm)
        self.assertIsInstance(response.context['email_form'], EmailUpdateForm)

    def test_settings_page_requires_login(self):
        """Test that settings page requires authentication"""
        self.client.logout()
        response = self.client.get(self.settings_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.settings_url}")

    def test_update_profile_success(self):
        """Test successful profile update (avatar and bio)"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.conf import settings
        import os
        
        # Create a test image file
        image_path = os.path.join(settings.MEDIA_ROOT, 'post_images', 'mountains.jpg')
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        avatar = SimpleUploadedFile('test_avatar.jpg', image_data, content_type='image/jpeg')
        data = {
            'bio': 'This is my new bio',
            'avatar': avatar
        }
        response = self.client.post(self.profile_settings_url, data)
        
        # Check redirect to settings page
        self.assertRedirects(response, self.settings_url)
        
        # Verify profile was updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'This is my new bio')
        self.assertTrue(self.profile.avatar)

    def test_update_avatar_only(self):
        """Test successful avatar update only"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.conf import settings
        import os
        
        # Create a test image file
        image_path = os.path.join(settings.MEDIA_ROOT, 'post_images', 'mountains.jpg')
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        avatar = SimpleUploadedFile('test_avatar.jpg', image_data, content_type='image/jpeg')
        data = {
            'bio': '',  # Keep same bio
            'avatar': avatar
        }
        response = self.client.post(self.profile_settings_url, data)
        
        # Check redirect to settings page
        self.assertRedirects(response, self.settings_url)
        
        # Verify avatar was updated
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.avatar)
        self.assertTrue(os.path.exists(self.profile.avatar.path))

    def test_update_profile_with_empty_data(self):
        """Test profile update with empty data (which is valid)"""
        data = {
            'bio': '',  # Valid but empty
            'avatar': ''  # Valid but empty
        }
        response = self.client.post(self.profile_settings_url, data)
        
        # Should redirect to settings page (form is valid)
        self.assertRedirects(response, self.settings_url)
        
        # Verify profile was updated (empty values are valid)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, '')

class ImageProcessingTests(TestCase):
    def setUp(self):
        # Create a test image
        self.img = Image.new('RGB', (400, 300), color='red')
        self.img_io = io.BytesIO()
        self.img.save(self.img_io, format='JPEG')
        self.img_io.seek(0)
        self.test_image = SimpleUploadedFile(
            'test.jpg',
            self.img_io.read(),
            content_type='image/jpeg'
        )

    def test_process_avatar_image_square(self):
        """Test avatar processing with square image"""
        # Create a square image
        img = Image.new('RGB', (300, 300), color='blue')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        square_image = SimpleUploadedFile(
            'square.jpg',
            img_io.read(),
            content_type='image/jpeg'
        )
        
        # Process the image
        processed = process_avatar_image(square_image)
        self.assertIsNotNone(processed)
        
        # Open and check the processed image
        img = Image.open(io.BytesIO(processed.read()))
        self.assertEqual(img.size, (300, 300))

    def test_process_avatar_image_landscape(self):
        """Test avatar processing with landscape image"""
        processed = process_avatar_image(self.test_image)
        self.assertIsNotNone(processed)
        
        # Open and check the processed image
        img = Image.open(io.BytesIO(processed.read()))
        self.assertEqual(img.size, (300, 300))

    def test_process_avatar_image_portrait(self):
        """Test avatar processing with portrait image"""
        # Create a portrait image
        img = Image.new('RGB', (300, 400), color='green')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        portrait_image = SimpleUploadedFile(
            'portrait.jpg',
            img_io.read(),
            content_type='image/jpeg'
        )
        
        processed = process_avatar_image(portrait_image)
        self.assertIsNotNone(processed)
        
        # Open and check the processed image
        img = Image.open(io.BytesIO(processed.read()))
        self.assertEqual(img.size, (300, 300))

    def test_process_avatar_image_with_transparency(self):
        """Test avatar processing with transparent PNG"""
        # Create a PNG with transparency
        img = Image.new('RGBA', (400, 300), color=(255, 0, 0, 0))
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        transparent_image = SimpleUploadedFile(
            'transparent.png',
            img_io.read(),
            content_type='image/png'
        )
        
        processed = process_avatar_image(transparent_image)
        self.assertIsNotNone(processed)
        
        # Open and check the processed image
        img = Image.open(io.BytesIO(processed.read()))
        self.assertEqual(img.size, (300, 300))
        self.assertEqual(img.mode, 'RGBA')

    def test_process_avatar_image_invalid(self):
        """Test avatar processing with invalid image data"""
        invalid_image = SimpleUploadedFile(
            'invalid.jpg',
            b'invalid image data',
            content_type='image/jpeg'
        )
        
        processed = process_avatar_image(invalid_image)
        self.assertIsNone(processed)

    def test_process_avatar_image_none(self):
        """Test avatar processing with None input"""
        processed = process_avatar_image(None)
        self.assertIsNone(processed)


class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        self.test_image = SimpleUploadedFile(
            'test_avatar.jpg',
            img_io.read(),
            content_type='image/jpeg'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            avatar=self.test_image
        )

    def test_delete_avatar(self):
        """Test avatar deletion method"""
        # Get the avatar path
        avatar_path = self.profile.avatar.path
        self.assertTrue(os.path.exists(avatar_path))
        
        # Delete the avatar
        self.profile.delete_avatar()
        
        # Check the file is gone
        self.assertFalse(os.path.exists(avatar_path))
        
        # Check the field is cleared
        self.profile.refresh_from_db()
        self.assertFalse(bool(self.profile.avatar))

    def test_delete_avatar_no_file(self):
        """Test avatar deletion when file doesn't exist"""
        # Remove the file but keep the field
        os.remove(self.profile.avatar.path)
        
        # Should not raise an error
        self.profile.delete_avatar()

    def test_profile_delete_signal(self):
        """Test avatar is deleted when profile is deleted"""
        avatar_path = self.profile.avatar.path
        self.assertTrue(os.path.exists(avatar_path))
        
        # Delete the profile
        self.profile.delete()
        
        # Check the file is gone
        self.assertFalse(os.path.exists(avatar_path))

    def test_user_delete_signal(self):
        """Test avatar is deleted when user is deleted"""
        avatar_path = self.profile.avatar.path
        self.assertTrue(os.path.exists(avatar_path))
        
        # Delete the user
        self.user.delete()
        
        # Check the file is gone
        self.assertFalse(os.path.exists(avatar_path))

    def test_avatar_update_signal(self):
        """Test old avatar is deleted when new one is uploaded"""
        old_avatar_path = self.profile.avatar.path
        
        # Create a new test image
        img = Image.new('RGB', (100, 100), color='blue')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        new_avatar = SimpleUploadedFile(
            'new_avatar.jpg',
            img_io.read(),
            content_type='image/jpeg'
        )
        
        # Update the avatar
        self.profile.avatar = new_avatar
        self.profile.save()
        
        # Check old file is gone and new file exists
        self.assertFalse(os.path.exists(old_avatar_path))
        self.assertTrue(os.path.exists(self.profile.avatar.path))


class FormAttributesTests(TestCase):
    def test_signup_form_attributes(self):
        """Test SignUpForm field attributes"""
        form = SignUpForm()
        for field in form.fields.values():
            self.assertEqual(field.widget.attrs['class'], 'form-control')

    def test_login_form_attributes(self):
        """Test CustomAuthenticationForm field attributes"""
        form = CustomAuthenticationForm()
        for field in form.fields.values():
            self.assertEqual(field.widget.attrs['class'], 'form-control')

    def test_password_change_form_attributes(self):
        """Test CustomPasswordChangeForm field attributes"""
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
        form = CustomPasswordChangeForm(user)
        for field in form.fields.values():
            self.assertEqual(field.widget.attrs['class'], 'form-control')

    def test_account_settings_form_attributes(self):
        """Test AccountSettingsForm field attributes"""
        form = AccountSettingsForm()
        
        # Check bio field attributes
        self.assertEqual(form.fields['bio'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['bio'].widget.attrs['rows'], 4)
        self.assertFalse(form.fields['bio'].required)
        
        # Check avatar field attributes
        self.assertEqual(form.fields['avatar'].widget.attrs['class'], 'hidden-file-input')
        self.assertEqual(form.fields['avatar'].widget.attrs['id'], 'avatar-input')
        self.assertEqual(form.fields['avatar'].widget.attrs['accept'], 'image/*')
        self.assertEqual(form.fields['avatar'].help_text, 'Upload a profile picture (optional)')
        self.assertFalse(form.fields['avatar'].required)

    def test_email_update_form_attributes(self):
        """Test EmailUpdateForm field attributes"""
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
        form = EmailUpdateForm(user=user)
        
        self.assertEqual(form.fields['email'].widget.attrs['class'], 'form-control')
        self.assertTrue(form.fields['email'].required)
        self.assertEqual(form.fields['email'].initial, 'test@example.com')


class EmailUpdateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.settings_url = reverse('accounts:settings')
        self.email_update_url = reverse('accounts:update_email')
        # Create and login a user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_email_update_success(self):
        """Test successful email update"""
        data = {
            'email': 'newemail@example.com'
        }
        response = self.client.post(self.email_update_url, data)
        
        # Check redirect to settings page
        self.assertRedirects(response, self.settings_url)
        
        # Verify email was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')

    def test_email_update_invalid_email(self):
        """Test email update with invalid email"""
        data = {
            'email': 'invalid-email'
        }
        response = self.client.post(self.email_update_url, data)
        
        # Check redirect to settings page (form errors are handled via messages)
        self.assertRedirects(response, self.settings_url)
        
        # Verify email was not updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'testuser@example.com')

    def test_email_update_requires_login(self):
        """Test that email update requires authentication"""
        self.client.logout()
        data = {
            'email': 'newemail@example.com'
        }
        response = self.client.post(self.email_update_url, data)
        
        # Should redirect to login page
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.email_update_url}")

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
        """Test successful account deletion with correct password"""
        response = self.client.post(self.delete_url, {'password': 'testpass123'})
        
        # Check redirect to home page
        self.assertRedirects(response, reverse('pages:index'))
        
        # Verify user and profile were deleted
        self.assertFalse(User.objects.filter(username='testuser').exists())
        self.assertFalse(Profile.objects.filter(user=self.user).exists())
        
        # Verify user is logged out
        response = self.client.get(reverse('accounts:settings'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:settings')}")

    def test_account_deletion_invalid_password(self):
        """Test account deletion with invalid password"""
        response = self.client.post(self.delete_url, {'password': 'wrongpassword'})
        
        # Should stay on the same page with error message
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/delete_confirm.html')
        
        # Verify user and profile still exist
        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_account_deletion_missing_password(self):
        """Test account deletion without password"""
        response = self.client.post(self.delete_url, {})
        
        # Should stay on the same page with error message
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/delete_confirm.html')
        
        # Verify user and profile still exist
        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_avatar_file_cleanup_on_deletion(self):
        """Test that avatar files are deleted when account is deleted"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.conf import settings
        import os
        
        # Create a test avatar file
        image_path = os.path.join(settings.MEDIA_ROOT, 'post_images', 'mountains.jpg')
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        avatar = SimpleUploadedFile('test_avatar.jpg', image_data, content_type='image/jpeg')
        self.profile.avatar = avatar
        self.profile.save()
        
        # Verify avatar file exists
        avatar_path = self.profile.avatar.path
        self.assertTrue(os.path.exists(avatar_path))
        
        # Delete the account
        response = self.client.post(self.delete_url, {'password': 'testpass123'})
        self.assertRedirects(response, reverse('pages:index'))
        
        # Verify avatar file was deleted
        self.assertFalse(os.path.exists(avatar_path))

    def test_account_deletion_requires_login(self):
        """Test that account deletion requires authentication"""
        self.client.logout()
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.delete_url}")
        
        # Verify user and profile still exist
        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertTrue(Profile.objects.filter(user=self.user).exists())