from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile

class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Please enter a correct username and password. Note that both fields may be case-sensitive.',
        'inactive': 'This account is inactive. Please check your email for the activation link.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create associated profile
            Profile.objects.create(user=user)
        return user

class AccountSettingsForm(forms.ModelForm):
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    
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
    email = forms.EmailField(required=True)
    
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
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})