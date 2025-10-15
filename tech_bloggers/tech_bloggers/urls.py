"""
URL configuration for tech_bloggers project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import GenericSitemap
from apps.blog.models import Post
from apps.blog.sitemaps import PostSitemap, TagSitemap, StaticViewSitemap
from two_factor.urls import urlpatterns as two_factor_urlpatterns

# Import admin configuration to apply custom branding
from . import admin_config

# Sitemap configuration
sitemaps = {
    'posts': PostSitemap,
    'tags': TagSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    # Redirect django-two-factor's /account/login/ to our styled login
    path('account/login/', RedirectView.as_view(pattern_name='accounts:login', permanent=False)),
    path('', include('apps.pages.urls')),
    path('blog/', include('apps.blog.urls')),
    path('accounts/', include('apps.accounts.urls')),
    
    # Include django-two-factor-auth URLs for admin login
    *two_factor_urlpatterns[0],  # Extract just the URL patterns from the tuple
    
    # Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
]

# Serve user-uploaded media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)