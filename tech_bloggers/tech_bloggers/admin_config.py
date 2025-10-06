from django.contrib import admin
from django.conf import settings

# Configure Django Admin site
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Django Administration')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Django site admin')
admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Site administration')
