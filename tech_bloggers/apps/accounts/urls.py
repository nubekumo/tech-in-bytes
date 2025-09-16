from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views
from .forms import CustomAuthenticationForm

app_name = 'accounts'

urlpatterns = [
    # Django's default auth URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # Password reset (forgot password)
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Account management
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('signup/done/', views.SignUpDoneView.as_view(), name='signup_done'),
    path('activate/<uidb64>/<token>/', views.ActivateAccountView.as_view(), name='activate'),
    path('activate/failed/', TemplateView.as_view(
        template_name='accounts/activation_failed.html'
    ), name='activation_failed'),
    path('settings/', views.AccountSettingsBaseView.as_view(), name='settings'),
    path('settings/update-profile/', views.UpdateProfileSettingsView.as_view(), name='update_profile'),
    path('settings/update-email/', views.UpdateEmailView.as_view(), name='update_email'),
    path('settings/update-password/', views.UpdatePasswordView.as_view(), name='update_password'),
    path('settings/delete-account/', views.DeleteAccountView.as_view(), name='delete_account'),
    
    # Temporary URL for email preview (remove in production)
    path('preview-activation-email/', views.preview_activation_email, name='preview_activation_email'),
]
