from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin


class SecureSessionMiddleware(MiddlewareMixin):
    """
    Middleware to ensure secure session handling and prevent
    cross-application session persistence
    """
    
    def process_request(self, request):
        # Check if user is accessing admin and ensure they're properly authenticated
        if request.path.startswith('/admin/'):
            # If user is accessing admin but not authenticated, clear any session data
            if not request.user.is_authenticated:
                request.session.flush()
        
        return None
    
    def process_response(self, request, response):
        # If user logged out from main app, ensure admin session is also cleared
        if hasattr(request, 'user') and isinstance(request.user, AnonymousUser):
            # Check if this is a logout request
            if request.path == '/accounts/logout/' and request.method == 'POST':
                # Clear all session data
                request.session.flush()
        
        return response
