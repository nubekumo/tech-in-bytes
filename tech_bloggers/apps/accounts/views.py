from django.views.generic import CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth import login, update_session_auth_hash, authenticate, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import PasswordChangeView
from .forms import CustomAuthenticationForm
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash, authenticate
import logging
from .models import Profile
from .forms import SignUpForm, AccountSettingsForm, CustomPasswordChangeForm

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
        logout(request)
        messages.success(request, "You have been successfully logged out.")
        return redirect('pages:index')

class CustomLoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        form = CustomAuthenticationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = CustomAuthenticationForm(data=request.POST)
        
        # Get credentials from the form
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        logger.info(f"Login attempt for username: {username}")
        
        try:
            # First check if user exists
            user = User.objects.get(username=username)
            logger.debug(f"User found. Active status: {user.is_active}")
            
            if not user.is_active:
                logger.info(f"Login attempt for inactive user: {username}")
                messages.error(request, "This account is inactive. Please check your email for the activation link.")
                return render(request, self.template_name, {'form': form})
            
            # Now try to authenticate
            user = authenticate(username=username, password=password)
            if user is not None:
                logger.info(f"Successful login for user: {username}")
                login(request, user)
                return redirect('pages:index')
            else:
                logger.info(f"Failed login attempt for user: {username} (invalid password)")
                messages.error(request, "Please enter a correct username and password. Note that both fields may be case-sensitive.")
                
        except User.DoesNotExist:
            logger.info(f"Login attempt for non-existent user: {username}")
            messages.error(request, "Please enter a correct username and password. Note that both fields may be case-sensitive.")
        
        return render(request, self.template_name, {'form': form})

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:signup_done')

    def post(self, request, *args, **kwargs):
        print("\nProcessing signup form submission:")
        print(f"POST data: {request.POST}")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        print("\nForm is valid, creating user...")
        try:
            # Create inactive user
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            print(f"Created user: {user.username} (id: {user.pk})")
            
            # Send activation email
            self.send_activation_email(user)
            
            return super().form_valid(form)
        except Exception as e:
            print(f"Error in form_valid: {str(e)}")
            raise

    def form_invalid(self, form):
        print("\nForm is invalid:")
        print(f"Form errors: {form.errors}")
        return super().form_invalid(form)
    
    def send_activation_email(self, user):
        try:
            print(f"\nSending activation email to {user.email}")
            current_site = get_current_site(self.request)
            print(f"Current site domain: {current_site.domain}")
            
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            print(f"Generated UID: {uid}")
            print(f"Generated token: {token}")
            
            mail_subject = 'Activate your Tech Bloggers account'
            message = render_to_string('accounts/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
            })
            
            email = EmailMessage(
                mail_subject, message, to=[user.email]
            )
            email.content_subtype = 'html'  # Main content is now HTML
            print("Attempting to send email...")
            email.send()
            print("Email sent successfully!")
            
        except Exception as e:
            print(f"Error sending activation email: {str(e)}")
            raise  # Re-raise the exception to handle it in the view

class SignUpDoneView(TemplateView):
    template_name = 'accounts/signup_done.html'

class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            # Debug print statements
            print(f"Activation attempt - uidb64: {uidb64}, token: {token}")
            
            uid = force_str(urlsafe_base64_decode(uidb64))
            print(f"Decoded UID: {uid}")
            
            user = User.objects.get(pk=uid)
            print(f"Found user: {user.username} (active: {user.is_active})")
            
            token_valid = account_activation_token.check_token(user, token)
            print(f"Token valid: {token_valid}")

            if token_valid:
                user.is_active = True
                user.save()
                login(request, user)
                messages.success(request, 'Your account has been activated. Welcome to Tech Bloggers!')
                return redirect('pages:index')
            else:
                messages.error(request, 'Activation link is invalid or has expired!')
                return redirect('accounts:activation_failed')
                
        except (TypeError, ValueError, OverflowError) as e:
            print(f"Error decoding UID: {str(e)}")
            messages.error(request, 'Invalid activation link format!')
            return redirect('accounts:activation_failed')
        except User.DoesNotExist:
            print(f"No user found with ID: {uid}")
            messages.error(request, 'User not found!')
            return redirect('accounts:activation_failed')

class AccountSettingsBaseView(LoginRequiredMixin, TemplateView):
    """Base view for the settings page - displays all forms"""
    template_name = 'accounts/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        context.update({
            'profile': profile,
            'settings_form': AccountSettingsForm(instance=profile),
            'password_form': CustomPasswordChangeForm(self.request.user),
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
        form.save()
        messages.success(self.request, 'Your account settings have been updated.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        # Include all forms in context for template reuse
        context = super().get_context_data(**kwargs)
        context['password_form'] = CustomPasswordChangeForm(self.request.user)
        return context

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

class DeleteAccountView(LoginRequiredMixin, DeleteView):
    """Handles account deletion with confirmation"""
    model = User
    template_name = 'accounts/delete_confirm.html'
    success_url = reverse_lazy('pages:index')
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Your account has been successfully deleted.')
        return super().delete(request, *args, **kwargs)

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