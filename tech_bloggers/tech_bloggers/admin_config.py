from django.conf import settings
from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError


class TechInBytesAdminAuthenticationForm(AdminAuthenticationForm):
    """Custom admin login form with clearer staff-only messaging."""

    permission_denied_message = (
        "You do not have permission to access the Admin site. "
        "Please sign in with an admin account or contact an administrator."
    )

    def confirm_login_allowed(self, user):
        # Preserve the default active-user validation from Django's auth form.
        AuthenticationForm.confirm_login_allowed(self, user)

        if not user.is_staff:
            raise ValidationError(
                self.permission_denied_message,
                code='no_staff_account',
            )


# Configure Django Admin site
admin.site.login_form = TechInBytesAdminAuthenticationForm
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Django Administration')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Django site admin')
admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Site administration')
