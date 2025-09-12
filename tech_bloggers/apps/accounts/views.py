from django.views.generic import CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Profile
from .forms import SignUpForm, AccountSettingsForm, CustomPasswordChangeForm

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import default_token_generator

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:signup_done')

    def form_valid(self, form):
        # Create inactive user
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        
        # Create profile
        Profile.objects.create(user=user)
        
        # Send activation email
        self.send_activation_email(user)
        
        return super().form_valid(form)
    
    def send_activation_email(self, user):
        current_site = get_current_site(self.request)
        mail_subject = 'Activate your Tech Bloggers account'
        message = render_to_string('accounts/activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        email = EmailMessage(
            mail_subject, message, to=[user.email]
        )
        email.content_subtype = 'html'  # Main content is now HTML
        email.send()

class SignUpDoneView(TemplateView):
    template_name = 'accounts/signup_done.html'

class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)
            messages.success(request, 'Your account has been activated. Welcome to Tech Bloggers!')
            return redirect('pages:index')
        else:
            messages.error(request, 'Activation link is invalid or has expired!')
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