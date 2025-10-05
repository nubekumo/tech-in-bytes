from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import Profile

class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Please enter a correct username and password. Note that both fields may be case-sensitive.',
        'inactive': 'This account is inactive. Please check your email for the activation link.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set max_length for username and password fields
        self.fields['username'].max_length = 150  # Django's default User model username max_length
        self.fields['password'].max_length = 128  # Reasonable limit for password input
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )
        return super().confirm_login_allowed(user)

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, max_length=254)
    first_name = forms.CharField(required=True, max_length=30, label='First Name')
    last_name = forms.CharField(required=True, max_length=30, label='Last Name')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set max_length for username and password fields
        self.fields['username'].max_length = 150  # Django's default User model username max_length
        self.fields['password1'].max_length = 128  # Reasonable limit for password input
        self.fields['password2'].max_length = 128  # Reasonable limit for password confirmation
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create associated profile
            Profile.objects.create(user=user)
        return user

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

class AccountSettingsForm(forms.ModelForm):
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False, max_length=500)
    
    class Meta:
        model = Profile
        fields = ('avatar', 'bio')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        # Add help text for avatar
        self.fields['avatar'].help_text = 'Upload a profile picture (optional)'
        self.fields['avatar'].widget.attrs.update({
            'id': 'avatar-input',
            'accept': 'image/*',
            'class': 'hidden-file-input'
        })
        
    def save(self, commit=True):
        profile = super().save(commit=commit)
        return profile

class EmailUpdateForm(forms.Form):
    email = forms.EmailField(required=True, max_length=254)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
    
    def save(self):
        if self.user:
            self.user.email = self.cleaned_data['email']
            self.user.save()
        return self.user

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set max_length for password fields
        self.fields['old_password'].max_length = 128
        self.fields['new_password1'].max_length = 128
        self.fields['new_password2'].max_length = 128
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(max_length=254)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})

class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set max_length for password fields
        self.fields['new_password1'].max_length = 128
        self.fields['new_password2'].max_length = 128
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})