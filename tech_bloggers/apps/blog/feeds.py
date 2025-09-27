from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.feedgenerator import Atom1Feed
from django.contrib.sites.shortcuts import get_current_site
from .models import Post


class LatestPostsFeed(Feed):
    """
    RSS feed for the latest published blog posts.
    Returns the 5 most recent published posts.
    """
    title = "Tech Bloggers - Latest Posts"
    description = "Latest posts from Tech Bloggers community"
    
    def link(self):
        return "/blog/"
    
    def items(self):
        """
        Return the 5 latest published posts ordered by publication date.
        """
        return Post.objects.filter(
            status='published'
        ).select_related('author').order_by('-published_at')[:5]
    
    def item_title(self, item):
        """Return the post title."""
        return item.title
    
    def item_description(self, item):
        """
        Return the post summary or truncated content.
        """
        if item.summary:
            return item.summary
        # If no summary, truncate content to 200 characters
        return item.content[:200] + "..." if len(item.content) > 200 else item.content
    
    def item_link(self, item):
        """
        Return the absolute URL to the post detail page.
        """
        return f"/blog/{item.pk}-{item.slug}/"
    
    def item_author_name(self, item):
        """
        Return the author's full name or username.
        """
        return item.author.get_full_name() or item.author.username
    
    def item_pubdate(self, item):
        """
        Return the publication date of the post.
        """
        return item.published_at
    
    def item_updateddate(self, item):
        """
        Return the last updated date of the post.
        """
        return item.updated_at
    
    def item_categories(self, item):
        """
        Return the tags associated with the post as categories.
        """
        return [tag.name for tag in item.tags.all()]


class LatestPostsAtomFeed(LatestPostsFeed):
    """
    Atom feed version of the latest posts feed.
    """
    feed_type = Atom1Feed
    subtitle = LatestPostsFeed.description
