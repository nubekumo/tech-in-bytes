from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Post
from taggit.models import Tag

class PostSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Post.objects.filter(status='published')

    def lastmod(self, obj):
        return obj.updated_at

class TagSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Tag.objects.all()

    def location(self, obj):
        return reverse('blog:tag_detail', args=[obj.slug])

class StaticViewSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return ['pages:index', 'pages:about', 'pages:contact']

    def location(self, item):
        return reverse(item)
