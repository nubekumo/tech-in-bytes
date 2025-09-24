from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Post, Tag


class PostListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test tags
        self.ai_tag = Tag.objects.create(name='AI', slug='ai')
        self.cyber_tag = Tag.objects.create(name='Cybersecurity', slug='cybersecurity')
        self.web_tag = Tag.objects.create(name='Web Development', slug='web-development')
        
        # Create a simple test image
        test_image = SimpleUploadedFile(
            "test_image.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        
        # Create test posts
        self.post1 = Post.objects.create(
            title='AI and Machine Learning',
            content='This is about AI and machine learning.',
            summary='AI post summary',
            author=self.user,
            status='published',
            image=test_image
        )
        self.post1.tags.add(self.ai_tag)
        
        self.post2 = Post.objects.create(
            title='Web Security Best Practices',
            content='This is about cybersecurity and web security.',
            summary='Security post summary',
            author=self.user,
            status='published',
            image=test_image
        )
        self.post2.tags.add(self.cyber_tag)
        
        self.post3 = Post.objects.create(
            title='React Development Guide',
            content='This is about React and web development.',
            summary='React post summary',
            author=self.user,
            status='published',
            image=test_image
        )
        self.post3.tags.add(self.web_tag)

    def test_post_list_view_loads(self):
        """Test that the post list view loads correctly."""
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'All Blog Posts')
        self.assertContains(response, self.post1.title)
        self.assertContains(response, self.post2.title)
        self.assertContains(response, self.post3.title)

    def test_search_functionality(self):
        """Test that search functionality works."""
        response = self.client.get(reverse('blog:post_list'), {'q': 'AI'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post1.title)
        self.assertNotContains(response, self.post2.title)
        self.assertNotContains(response, self.post3.title)

    def test_category_filter(self):
        """Test that category filtering works."""
        response = self.client.get(reverse('blog:post_list'), {'category': 'ai'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post1.title)
        self.assertNotContains(response, self.post2.title)
        self.assertNotContains(response, self.post3.title)

    def test_combined_search_and_filter(self):
        """Test that search and category filter work together."""
        response = self.client.get(reverse('blog:post_list'), {'q': 'security', 'category': 'cybersecurity'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post2.title)
        self.assertNotContains(response, self.post1.title)
        self.assertNotContains(response, self.post3.title)

    def test_empty_search_results(self):
        """Test empty search results."""
        response = self.client.get(reverse('blog:post_list'), {'q': 'nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No posts found')
        self.assertNotContains(response, self.post1.title)
        self.assertNotContains(response, self.post2.title)
        self.assertNotContains(response, self.post3.title)
