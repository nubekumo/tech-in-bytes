"""
URL configuration for tech_bloggers project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import GenericSitemap
from apps.blog.models import Post
from apps.blog.sitemaps import PostSitemap, TagSitemap, StaticViewSitemap

# Sitemap configuration
sitemaps = {
    'posts': PostSitemap,
    'tags': TagSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.pages.urls')),
    path('blog/', include('apps.blog.urls')),
    path('accounts/', include('apps.accounts.urls')),
    
    
    # Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
]

# Serve user-uploaded media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)