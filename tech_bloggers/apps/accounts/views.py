from django.views.generic import CreateView, UpdateView, DeleteView, TemplateView, View
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth import login, update_session_auth_hash, authenticate, logout
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetView, PasswordResetConfirmView
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from .forms import CustomAuthenticationForm, CustomPasswordResetForm, CustomSetPasswordForm
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash, authenticate
import logging
from .models import Profile
from .forms import SignUpForm, AccountSettingsForm, EmailUpdateForm, CustomPasswordChangeForm
from .utils import process_avatar_image

# 2FA imports
from django_otp.decorators import otp_required
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.util import random_hex
from django.http import JsonResponse
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64

# Get an instance of a logger
logger = logging.getLogger(__name__)

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import PasswordResetTokenGenerator

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk) + str(timestamp) + str(user.is_active)
        )

account_activation_token = AccountActivationTokenGenerator()
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

class LogoutView(View):
    def post(self, request):
        logger.info(f"Logout request for user: {request.user.username}")
        
        # Clear all session data to ensure complete logout
        request.session.flush()
        
        # Perform Django logout
        logout(request)
        
        messages.success(request, "You have been successfully logged out.")
        return redirect('pages:index')

@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='dispatch')
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = CustomAuthenticationForm
    
    def get_success_url(self):
        """Override to handle admin redirects properly."""
        next_url = self.request.GET.get('next')
        if next_url and '/admin/' in next_url:
            return next_url
        return super().get_success_url()
    
    def form_valid(self, form):
        """Override form_valid to handle 2FA verification."""
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        # Authenticate the user (pass request for AxesBackend compatibility)
        user = authenticate(request=self.request, username=username, password=password)
        
        if user is not None:
            # Check if trying to access admin
            next_url = self.request.GET.get('next', '')
            if '/admin/' in next_url and not user.is_staff:
                # Non-staff user trying to access admin
                form.add_error(None, ValidationError(
                    "You do not have permission to access the Admin site. "
                    "Please sign in with an admin account or contact an administrator.",
                    code='no_staff_account',
                ))
                return self.form_invalid(form)
            
            # Check if user has 2FA enabled
            if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
                # User has 2FA enabled, redirect to 2FA verification
                logger.info(f"User {username} has 2FA enabled, redirecting to verification")
                
                # Store user ID and next URL in session for 2FA verification
                self.request.session['2fa_user_id'] = user.id
                next_url = self.request.GET.get('next')
                if next_url:
                    self.request.session['2fa_next_url'] = next_url
                
                # Redirect to 2FA verification page
                return redirect('accounts:two_factor_verify')
            else:
                # No 2FA, proceed with normal login
                logger.info(f"Successful login for user: {username} (no 2FA)")
                login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect(self.get_success_url())
        else:
            logger.info(f"Failed login attempt for user: {username}")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Override form_invalid to add logging."""
        username = form.cleaned_data.get('username')
        logger.info(f"Failed login attempt for user: {username}")
        return super().form_invalid(form)

@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:signup_done')

    def post(self, request, *args, **kwargs):
        # Track if the form submission is successful without logging sensitive data
        logger.debug("Processing signup form submission")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # Track if the form is valid
        logger.debug("Form is valid, creating user...")
        try:
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            logger.info(f"Created user: {user.username} (id: {user.pk})")
            
            self.send_activation_email(user)
            
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error in form_valid: {str(e)}")
            raise

    def form_invalid(self, form):
        # Track if the form is invalid
        logger.warning("Form is invalid")
        logger.debug(f"Form errors: {form.errors}")
        return super().form_invalid(form)
    
    def send_activation_email(self, user):
        try:
            # Track if the activation email is sent
            logger.debug(f"Sending activation email to {user.email}")
            current_site = get_current_site(self.request)
            logger.debug(f"Current site domain: {current_site.domain}")
            
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            # Do not log UID/token values
            
            # Build absolute activation URL
            from django.urls import reverse
            activation_path = reverse('accounts:activate', kwargs={'uidb64': uid, 'token': token})
            activation_url = self.request.build_absolute_uri(activation_path)

            mail_subject = 'Activate your Tech-In-Bytes account'
            message = render_to_string('accounts/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'protocol': 'https' if self.request.is_secure() else 'http',
                'activation_url': activation_url,
            })
            
            email = EmailMessage(
                mail_subject, message, to=[user.email]
            )
            email.content_subtype = 'html'
            logger.debug("Attempting to send activation email...")
            email.send()
            logger.info("Activation email sent successfully!")
            
        except Exception as e:
            logger.error(f"Error sending activation email: {str(e)}")
            raise

@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    form_class = CustomPasswordResetForm
    
    def form_valid(self, form):
        """Override form_valid to use EmailMessage for HTML emails."""
        logger.debug("Password reset form submitted")
        
        # Get the email
        email = form.cleaned_data["email"]
        logger.debug(f"Processing password reset for email: {email}")
        
        # Get active users (built-in PasswordResetView has get_users helper)
        active_users = list(self.get_users(email)) if hasattr(self, 'get_users') else list(User.objects.filter(email__iexact=email, is_active=True))
        logger.debug(f"Found {len(active_users)} active users with this email")
        
        # If no users matched, render the same page with a friendly info
        if not active_users:
            logger.info("No account found for submitted email; showing inline info message")
            context = self.get_context_data(form=form, email_not_found=True)
            return self.render_to_response(context)

        try:
            for user in active_users:
                # Generate token
                current_site = get_current_site(self.request)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                logger.debug(f"Generated reset token for user: {user.username}")
                
                # Create context
                context = {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': uid,
                    'token': token,
                    'protocol': 'http',  # or 'https' for production
                }
                
                # Render email content
                subject = render_to_string(self.subject_template_name, context).strip()
                message = render_to_string(self.email_template_name, context)
                logger.debug("Email templates rendered successfully")
                
                # Send email using EmailMessage
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    to=[user.email],
                )
                email.content_subtype = 'html' 
                email.send()
                
                logger.info(f"Password reset email sent to {user.email}")
                
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            raise
        
        logger.info("Password reset process completed successfully")
        # Avoid calling super().form_valid which would send a second email.
        return redirect(self.get_success_url())


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    form_class = CustomSetPasswordForm

    def form_valid(self, form):
        try:
            # The view sets self.user to the user whose password is being reset
            target_username = getattr(self, 'user', None).get_username() if getattr(self, 'user', None) else '(unknown)'
            logger.info(f"Setting new password for user: {target_username}")
        except Exception:
            logger.info("Setting new password for user: (unavailable)")
        return super().form_valid(form)


class SignUpDoneView(TemplateView):
    template_name = 'accounts/signup_done.html'

class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            # Track activation attempt without logging sensitive token/uid
            logger.debug("Activation attempt received")
            
            uid = force_str(urlsafe_base64_decode(uidb64))
            # Do not log decoded UID value
            
            user = User.objects.get(pk=uid)
            logger.debug(f"Found user: {user.username} (active: {user.is_active})")
            
            token_valid = account_activation_token.check_token(user, token)
            logger.debug("Token validity checked")

            if token_valid:
                user.is_active = True
                user.save()
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                logger.info(f"Account activated successfully for user: {user.username}")
                messages.success(request, 'Your account has been activated. Welcome to Tech Bloggers!')
                return redirect('pages:index')
            else:
                # If account is already active, treat as success to avoid confusing UX
                if user.is_active:
                    logger.info(f"Activation link used for already activated user: {user.username}")
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.info(request, 'Your account is already activated. Welcome back!')
                    return redirect('pages:index')
                logger.warning(f"Invalid or expired activation token for user: {user.username}")
                messages.error(request, 'Activation link is invalid or has expired!')
                return redirect('accounts:activation_failed')
                
        except (TypeError, ValueError, OverflowError) as e:
            logger.error(f"Error decoding UID: {str(e)}")
            messages.error(request, 'Invalid activation link format!')
            return redirect('accounts:activation_failed')
        except User.DoesNotExist:
            logger.error(f"No user found with ID: {uid}")
            messages.error(request, 'User not found!')
            return redirect('accounts:activation_failed')

class AccountSettingsBaseView(LoginRequiredMixin, TemplateView):
    """Base view for the settings page - displays all forms"""
    template_name = 'accounts/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        settings_form = AccountSettingsForm(instance=profile)
        
        # Check 2FA status
        has_2fa = TOTPDevice.objects.filter(user=self.request.user, confirmed=True).exists()
        
        context.update({
            'profile': profile,
            'form': settings_form,
            'email_form': EmailUpdateForm(user=self.request.user),
            'password_form': CustomPasswordChangeForm(self.request.user),
            'has_2fa': has_2fa,
        })
        return context

class UpdateProfileSettingsView(LoginRequiredMixin, UpdateView):
    """Handles profile settings updates (email and avatar)"""
    model = Profile
    form_class = AccountSettingsForm
    template_name = 'accounts/settings.html'
    success_url = reverse_lazy('accounts:settings')
    
    def get_object(self, queryset=None):
        return Profile.objects.get_or_create(user=self.request.user)[0]
    
    def form_valid(self, form):
        logger.info(f"Profile form is valid. Data: {form.cleaned_data}")
        # Save instance without committing to allow avatar processing
        profile = form.save(commit=False)

        # Process avatar only if user uploaded a new file in this submission
        avatar_file = self.request.FILES.get('avatar')

        if avatar_file:
            # Get drag offset values from POST data
            try:
                offset_x = float(self.request.POST.get('avatar_offset_x', 0))
                offset_y = float(self.request.POST.get('avatar_offset_y', 0))
            except (ValueError, TypeError):
                offset_x = 0
                offset_y = 0
            
            processed = process_avatar_image(
                avatar_file,
                size=(300, 300),
                offset_x=offset_x,
                offset_y=offset_y,
            )
            if processed is not None:
                # Use the processed file's own name to keep correct extension/mimetype
                profile.avatar.save(getattr(processed, 'name', 'avatar.jpg'), processed, save=False)
                logger.info("Avatar processed and set on profile")
            else:
                logger.warning("Avatar processing failed; using original upload")
                # Fallback to saving the original upload
                profile.avatar = avatar_file

        # Persist other fields (e.g., bio)
        profile.save()
        self.object = profile
        logger.info(f"Profile saved: {profile}")
        messages.success(self.request, 'Your account settings have been updated.')
        return redirect(self.get_success_url())
    
    def form_invalid(self, form):
        logger.warning(f"Profile form is invalid. Errors: {form.errors}")
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        # Include all forms in context for template reuse
        context = super().get_context_data(**kwargs)
        context['password_form'] = CustomPasswordChangeForm(self.request.user)
        return context

class UpdateEmailView(LoginRequiredMixin, View):
    """Handles email updates"""
    
    def post(self, request):
        form = EmailUpdateForm(request.POST, user=request.user)
        if form.is_valid():
            logger.info(f"Email form is valid. Data: {form.cleaned_data}")
            form.save()
            messages.success(request, 'Your email has been updated.')
        else:
            logger.warning(f"Email form is invalid. Errors: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
        return redirect('accounts:settings')

class UpdatePasswordView(LoginRequiredMixin, PasswordChangeView):
    """Handles password changes"""
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/settings.html'
    success_url = reverse_lazy('accounts:settings')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, 'Your password has been updated.')
        return response
    
    def get_context_data(self, **kwargs):
        # Include all forms in context for template reuse
        context = super().get_context_data(**kwargs)
        profile = Profile.objects.get_or_create(user=self.request.user)[0]
        context['settings_form'] = AccountSettingsForm(instance=profile)
        return context

class DeleteAccountView(LoginRequiredMixin, View):
    """Handles account deletion with confirmation"""
    template_name = 'accounts/delete_confirm.html'
    
    def get(self, request):
        """Show the delete confirmation page"""
        return render(request, self.template_name)
    
    def post(self, request):
        """Handle the actual account deletion"""
        # Verify password before deletion
        password = request.POST.get('password', '')
        user = request.user
        
        if not user.check_password(password):
            messages.error(request, 'Invalid password. Please try again.')
            return render(request, self.template_name)
        
        # Delete the user account
        username = user.username
        user.delete()
        
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('pages:index')

def preview_activation_email(request):
    """Temporary view to preview activation email template"""
    if not request.user.is_superuser:
        raise PermissionDenied
    
    context = {
        'user': request.user,
        'domain': request.get_host(),
        'uid': urlsafe_base64_encode(force_bytes(request.user.pk)),
        'token': account_activation_token.make_token(request.user),
    }
    return render(request, 'accounts/activation_email.html', context)


# 2FA Views
class TwoFactorSetupView(LoginRequiredMixin, View):
    """View to setup 2FA for a user"""
    template_name = 'accounts/two_factor_setup.html'
    
    def get(self, request):
        # Check if user already has 2FA enabled
        if TOTPDevice.objects.filter(user=request.user, confirmed=True).exists():
            messages.info(request, 'Two-factor authentication is already enabled for your account.')
            return redirect('accounts:settings')
        
        # Get or create TOTP device
        device, created = TOTPDevice.objects.get_or_create(
            user=request.user,
            defaults={'name': 'default', 'confirmed': False}
        )
        
        if not device.key:
            device.key = device.generate_key()
            device.save()
        
        # Generate QR code
        qr_code = self.generate_qr_code(request, device)
        
        context = {
            'device': device,
            'qr_code': qr_code,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Verify the TOTP token and enable 2FA"""
        token = request.POST.get('token', '').strip()
        
        if not token:
            messages.error(request, 'Please enter a verification code.')
            return redirect('accounts:two_factor_setup')
        
        # Get the device
        device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
        if not device:
            messages.error(request, 'No pending 2FA setup found.')
            return redirect('accounts:settings')
        
        # Verify the token
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            
            # Generate backup tokens
            self.generate_backup_tokens(request.user)
            
            messages.success(request, 'Two-factor authentication has been enabled successfully!')
            logger.info(f"2FA enabled for user: {request.user.username}")
            return redirect('accounts:two_factor_backup_tokens')
        else:
            messages.error(request, 'Invalid verification code. Please try again.')
            return redirect('accounts:two_factor_setup')
    
    def generate_qr_code(self, request, device):
        """Generate QR code for TOTP setup"""
        # Create the TOTP URI
        totp_uri = device.config_url
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # Create SVG image
        img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer)
        qr_code_data = buffer.getvalue()
        qr_code_base64 = base64.b64encode(qr_code_data).decode()
        
        return f"data:image/svg+xml;base64,{qr_code_base64}"
    
    def generate_backup_tokens(self, user):
        """Generate backup tokens for the user"""
        # Delete existing backup tokens
        StaticDevice.objects.filter(user=user, name='backup').delete()
        
        # Create new backup tokens
        device = StaticDevice.objects.create(user=user, name='backup')
        device.token_set.create(token=random_hex(8))
        device.token_set.create(token=random_hex(8))
        device.token_set.create(token=random_hex(8))
        device.token_set.create(token=random_hex(8))
        device.token_set.create(token=random_hex(8))


class TwoFactorQRView(LoginRequiredMixin, View):
    """View to display QR code for 2FA setup"""
    
    def get(self, request):
        device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
        if not device:
            return JsonResponse({'error': 'No pending 2FA setup'}, status=400)
        
        # Generate QR code
        qr_code = self.generate_qr_code(request, device)
        return JsonResponse({'qr_code': qr_code})
    
    def generate_qr_code(self, request, device):
        """Generate QR code for TOTP setup"""
        totp_uri = device.config_url
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
        
        buffer = BytesIO()
        img.save(buffer)
        qr_code_data = buffer.getvalue()
        qr_code_base64 = base64.b64encode(qr_code_data).decode()
        
        return f"data:image/svg+xml;base64,{qr_code_base64}"


class TwoFactorBackupTokensView(LoginRequiredMixin, View):
    """View to display backup tokens"""
    template_name = 'accounts/two_factor_backup_tokens.html'
    
    def get(self, request):
        # Get backup tokens
        device = StaticDevice.objects.filter(user=request.user, name='backup').first()
        if not device:
            messages.error(request, 'No backup tokens found.')
            return redirect('accounts:settings')
        
        tokens = list(device.token_set.values_list('token', flat=True))
        
        context = {
            'tokens': tokens,
        }
        return render(request, self.template_name, context)


class TwoFactorDisableView(LoginRequiredMixin, View):
    """View to disable 2FA"""
    
    def post(self, request):
        # Verify password before disabling
        password = request.POST.get('password', '')
        if not request.user.check_password(password):
            messages.error(request, 'Invalid password. Please try again.')
            return redirect('accounts:settings')
        
        # Delete TOTP devices
        TOTPDevice.objects.filter(user=request.user).delete()
        
        # Delete backup tokens
        StaticDevice.objects.filter(user=request.user, name='backup').delete()
        
        messages.success(request, 'Two-factor authentication has been disabled.')
        logger.info(f"2FA disabled for user: {request.user.username}")
        return redirect('accounts:settings')


class TwoFactorVerifyView(View):
    """View to verify 2FA token during login"""
    template_name = 'accounts/two_factor_verify.html'
    
    def get(self, request):
        # Check if user ID is in session
        user_id = request.session.get('2fa_user_id')
        if not user_id:
            messages.error(request, 'Please log in first.')
            return redirect('accounts:login')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'Invalid session. Please log in again.')
            request.session.pop('2fa_user_id', None)
            return redirect('accounts:login')
        
        # Check if user still has 2FA enabled
        if not TOTPDevice.objects.filter(user=user, confirmed=True).exists():
            messages.info(request, '2FA is no longer enabled for your account.')
            request.session.pop('2fa_user_id', None)
            return redirect('accounts:login')
        
        return render(request, self.template_name)
    
    def post(self, request):
        # Check if user ID is in session
        user_id = request.session.get('2fa_user_id')
        if not user_id:
            messages.error(request, 'Please log in first.')
            return redirect('accounts:login')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'Invalid session. Please log in again.')
            request.session.pop('2fa_user_id', None)
            return redirect('accounts:login')
        
        # Get the token from the form
        token = request.POST.get('token', '').strip()
        
        if not token:
            messages.error(request, 'Please enter a verification code.')
            return render(request, self.template_name)
        
        # Get the user's TOTP device
        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if not device:
            messages.error(request, '2FA device not found. Please contact support.')
            request.session.pop('2fa_user_id', None)
            return redirect('accounts:login')
        
        # Verify the token
        if device.verify_token(token):
            # Token is valid, get the stored next URL before clearing session
            next_url = request.session.get('2fa_next_url')
            
            # Check if trying to access admin and user is not staff
            if next_url and '/admin/' in next_url and not user.is_staff:
                # Non-staff user trying to access admin after 2FA
                messages.error(request, 
                    "You do not have permission to access the Admin site. "
                    "Please sign in with an admin account or contact an administrator.")
                request.session.pop('2fa_user_id', None)
                request.session.pop('2fa_next_url', None)
                return redirect('accounts:login')
            
            # Log the user in
            # Use the ModelBackend specifically to avoid backend conflicts
            from django.contrib.auth.backends import ModelBackend
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session.pop('2fa_user_id', None)
            request.session.pop('2fa_next_url', None)
            
            # Determine redirect URL
            if next_url and '/admin/' in next_url:
                redirect_url = next_url
            else:
                redirect_url = 'pages:index'
            
            messages.success(request, 'Login successful!')
            logger.info(f"2FA verification successful for user: {user.username}")
            return redirect(redirect_url)
        else:
            # Token is invalid
            messages.error(request, 'Invalid verification code. Please try again.')
            logger.warning(f"Invalid 2FA token for user: {user.username}")
            return render(request, self.template_name)


class AdminLogoutView(View):
    """Custom admin logout view to ensure complete session clearing"""
    
    def get(self, request):
        # Clear all session data to ensure complete logout
        request.session.flush()
        
        # Perform Django logout
        logout(request)
        
        # Redirect to admin login page
        return redirect('admin:login')