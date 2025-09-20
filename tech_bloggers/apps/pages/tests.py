from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
from apps.blog.models import Post, Tag


class IndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='author1',
            email='author1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='author2',
            email='author2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='author3',
            email='author3@example.com',
            password='testpass123'
        )
        
        # Create test tags
        self.ai_tag = Tag.objects.create(name='AI', slug='ai')
        self.cyber_tag = Tag.objects.create(name='Cybersecurity', slug='cybersecurity')
        
        # Create a simple test image
        test_image = SimpleUploadedFile(
            "test_image.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        
        # Create test posts with different publish dates
        now = timezone.now()
        
        # Post with 3 likes (most liked)
        self.post_most_liked = Post.objects.create(
            title='Most Liked Post',
            content='This post has the most likes.',
            summary='Most liked post summary',
            author=self.user1,
            status='published',
            image=test_image,
            published_at=now - timedelta(days=5)
        )
        self.post_most_liked.tags.add(self.ai_tag)
        
        # Post with 2 likes (second most liked)
        self.post_second_liked = Post.objects.create(
            title='Second Most Liked Post',
            content='This post has the second most likes.',
            summary='Second most liked post summary',
            author=self.user2,
            status='published',
            image=test_image,
            published_at=now - timedelta(days=3)
        )
        self.post_second_liked.tags.add(self.cyber_tag)
        
        # Post with 2 likes but more recent (should come before post_second_liked due to tie-breaking)
        self.post_tied_likes_recent = Post.objects.create(
            title='Tied Likes Recent Post',
            content='This post has same likes but more recent.',
            summary='Tied likes recent post summary',
            author=self.user3,
            status='published',
            image=test_image,
            published_at=now - timedelta(days=1)
        )
        self.post_tied_likes_recent.tags.add(self.ai_tag)
        
        # Post with 1 like
        self.post_one_like = Post.objects.create(
            title='One Like Post',
            content='This post has one like.',
            summary='One like post summary',
            author=self.user1,
            status='published',
            image=test_image,
            published_at=now - timedelta(days=2)
        )
        self.post_one_like.tags.add(self.cyber_tag)
        
        # Post with 0 likes (should not appear in most liked)
        self.post_no_likes = Post.objects.create(
            title='No Likes Post',
            content='This post has no likes.',
            summary='No likes post summary',
            author=self.user2,
            status='published',
            image=test_image,
            published_at=now - timedelta(days=4)
        )
        self.post_no_likes.tags.add(self.ai_tag)
        
        # Draft post (should not appear in most liked)
        self.draft_post = Post.objects.create(
            title='Draft Post',
            content='This is a draft post.',
            summary='Draft post summary',
            author=self.user3,
            status='draft',
            image=test_image,
            published_at=now - timedelta(days=1)
        )
        self.draft_post.tags.add(self.cyber_tag)
        
        # Add likes to posts
        self.post_most_liked.likes.add(self.user1, self.user2, self.user3)
        self.post_second_liked.likes.add(self.user1, self.user2)
        self.post_tied_likes_recent.likes.add(self.user1, self.user2)
        self.post_one_like.likes.add(self.user1)

    def test_index_view_loads(self):
        """Test that the index view loads correctly."""
        response = self.client.get(reverse('pages:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Stay Ahead with Tech Insights')

    def test_most_liked_posts_ordering(self):
        """Test that posts are ordered by like count (descending), then by publish date (descending)."""
        response = self.client.get(reverse('pages:index'))
        self.assertEqual(response.status_code, 200)
        
        recommended_posts = response.context['recommended_posts']
        
        # Should have 3 posts (limit is 3)
        self.assertEqual(len(recommended_posts), 3)
        
        # Check ordering: most liked first, then by publish date for ties
        self.assertEqual(recommended_posts[0], self.post_most_liked)  # 3 likes
        self.assertEqual(recommended_posts[1], self.post_tied_likes_recent)  # 2 likes, more recent
        self.assertEqual(recommended_posts[2], self.post_second_liked)  # 2 likes, older

    def test_most_liked_posts_limit(self):
        """Test that only 3 most liked posts are returned."""
        response = self.client.get(reverse('pages:index'))
        self.assertEqual(response.status_code, 200)
        
        recommended_posts = response.context['recommended_posts']
        self.assertEqual(len(recommended_posts), 3)

    def test_most_liked_posts_only_published(self):
        """Test that only published posts are included in most liked posts."""
        response = self.client.get(reverse('pages:index'))
        self.assertEqual(response.status_code, 200)
        
        recommended_posts = response.context['recommended_posts']
        
        # Check that draft post is not included
        draft_post_ids = [post.id for post in recommended_posts if post.status == 'draft']
        self.assertEqual(len(draft_post_ids), 0)
        
        # Check that all returned posts are published
        for post in recommended_posts:
            self.assertEqual(post.status, 'published')

    def test_most_liked_posts_excludes_zero_likes(self):
        """Test that posts with 0 likes are not included when there are posts with likes."""
        response = self.client.get(reverse('pages:index'))
        self.assertEqual(response.status_code, 200)
        
        recommended_posts = response.context['recommended_posts']
        
        # Check that post with 0 likes is not included
        zero_like_post_ids = [post.id for post in recommended_posts if post.likes.count() == 0]
        self.assertEqual(len(zero_like_post_ids), 0)

    def test_most_liked_posts_tie_breaking(self):
        """Test that posts with same like count are ordered by publish date (most recent first)."""
        response = self.client.get(reverse('pages:index'))
        self.assertEqual(response.status_code, 200)
        
        recommended_posts = response.context['recommended_posts']
        
        # Find posts with 2 likes
        posts_with_2_likes = [post for post in recommended_posts if post.likes.count() == 2]
        
        if len(posts_with_2_likes) >= 2:
            # More recent post should come first
            self.assertGreaterEqual(
                posts_with_2_likes[0].published_at,
                posts_with_2_likes[1].published_at
            )

    def test_most_liked_posts_context_variable(self):
        """Test that recommended_posts context variable contains the correct posts."""
        response = self.client.get(reverse('pages:index'))
        self.assertEqual(response.status_code, 200)
        
        # Check that context variable exists
        self.assertIn('recommended_posts', response.context)
        
        recommended_posts = response.context['recommended_posts']
        self.assertIsNotNone(recommended_posts)

    def test_most_liked_posts_template_display(self):
        """Test that the template displays the most liked posts section correctly."""
        response = self.client.get(reverse('pages:index'))
        self.assertEqual(response.status_code, 200)
        
        # Check that the section title is correct
        self.assertContains(response, 'Most Liked Posts')
        
        # Check that like counts are displayed
        self.assertContains(response, '3 likes')  # Most liked post
        self.assertContains(response, '2 likes')  # Posts with 2 likes
        # Note: Post with 1 like may not appear if there are 3+ posts with 2+ likes

    def test_most_liked_posts_with_no_posts(self):
        """Test behavior when there are no published posts."""
        # Delete all posts
        Post.objects.all().delete()
        
        response = self.client.get(reverse('pages:index'))
        self.assertEqual(response.status_code, 200)
        
        recommended_posts = response.context['recommended_posts']
        self.assertEqual(len(recommended_posts), 0)

    def test_most_liked_posts_with_all_zero_likes(self):
        """Test behavior when all posts have 0 likes."""
        # Remove all likes
        for post in Post.objects.all():
            post.likes.clear()
        
        response = self.client.get(reverse('pages:index'))
        self.assertEqual(response.status_code, 200)
        
        recommended_posts = response.context['recommended_posts']
        
        # Should still return up to 3 posts, ordered by publish date
        self.assertLessEqual(len(recommended_posts), 3)
        
        # All posts should have 0 likes
        for post in recommended_posts:
            self.assertEqual(post.likes.count(), 0)
