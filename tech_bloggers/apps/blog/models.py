from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete
from django.dispatch import receiver
from PIL import Image, UnidentifiedImageError
from django.conf import settings
import os

def validate_image(image):
    # Size in bytes
    max_bytes = getattr(settings, 'IMAGE_MAX_UPLOAD_MB', 2) * 1024 * 1024
    if image.size and image.size > max_bytes:
        raise ValidationError(f"Image too large. Max size is {getattr(settings, 'IMAGE_MAX_UPLOAD_MB', 2)}MB.")

    allowed_formats = {"JPEG", "JPG", "PNG", "WEBP"}
    max_width = getattr(settings, 'IMAGE_MAX_WIDTH', 2048)
    max_height = getattr(settings, 'IMAGE_MAX_HEIGHT', 2048)
    max_pixels = getattr(settings, 'IMAGE_MAX_PIXELS', 12000000)

    try:
        with Image.open(image) as img:
            # Verify basic image integrity by accessing size/format
            fmt = (img.format or '').upper()
            if fmt not in allowed_formats:
                raise ValidationError("Unsupported image format. Use JPEG, PNG, or WebP.")

            width, height = img.size
            if width <= 0 or height <= 0:
                raise ValidationError("Invalid image dimensions.")

            # Pixel bomb protection
            if (width * height) > max_pixels:
                raise ValidationError("Image resolution too large.")

            # Dimension limits
            if width > max_width or height > max_height:
                raise ValidationError("Image dimensions exceed allowed maximum.")
    except UnidentifiedImageError:
        raise ValidationError("Invalid image file.")
    except OSError:
        raise ValidationError("Invalid or corrupted image file.")
    finally:
        try:
            # Reset file pointer for subsequent consumers
            if hasattr(image, 'seek'):
                image.seek(0)
        except Exception:
            pass
    

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    

class Post(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("published", "Published")]
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField(max_length=50000)  # Reasonable limit for blog content
    summary = models.TextField(blank=True, max_length=1000)  # Reasonable limit for summary
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blog_posts")
    tags = models.ManyToManyField(Tag, blank=True)
    image = models.ImageField(upload_to="post_images/", blank=True, null=True, validators=[validate_image])
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-published_at']
        indexes = [models.Index(fields=['published_at'])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    @property
    def top_level_comment_count(self):
        """Return the count of top-level comments (excluding replies)"""
        return self.comments.filter(parent__isnull=True).count()
    

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=2000)  # Reasonable limit for comments
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created_at']
        indexes = [models.Index(fields=['created_at'])]

    def __str__(self):
        return f"Comment by {self.author} on {self.post}."


class PostImage(models.Model):
    """
    Model for images uploaded within blog post content via TinyMCE
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='content_images', null=True, blank=True)
    image = models.ImageField(upload_to='post_images/content/', validators=[validate_image])
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alternative text for accessibility")
    original_filename = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['post', 'uploaded_at']),
            models.Index(fields=['uploaded_by'])
        ]

    def __str__(self):
        if self.post:
            return f"Image for {self.post.title} by {self.uploaded_by.username}"
        else:
            return f"Temporary image by {self.uploaded_by.username}"

    def save(self, *args, **kwargs):
        # Store original filename if not already set
        if not self.original_filename and self.image:
            self.original_filename = self.image.name
        super().save(*args, **kwargs)


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['user', 'post']),
            models.Index(fields=['created_at'])
        ]

    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"


@receiver(post_delete, sender=Post)
def delete_post_image_file(sender, instance, **kwargs):
    """
    Delete the post image file from the filesystem when a Post instance is deleted.
    """
    if instance.image:
        try:
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
        except (ValueError, OSError):
            # Handle cases where the file might not exist or path is invalid
            pass


@receiver(post_delete, sender=PostImage)
def delete_post_content_image_file(sender, instance, **kwargs):
    """
    Delete the content image file from the filesystem when a PostImage instance is deleted.
    """
    if instance.image:
        try:
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
        except (ValueError, OSError):
            # Handle cases where the file might not exist or path is invalid
            pass


@receiver(post_delete, sender=Post)
def delete_orphaned_post_images(sender, instance, **kwargs):
    """
    Delete orphaned PostImage records when a Post is deleted.
    This is a backup cleanup in case the CASCADE doesn't work properly.
    """
    from .models import PostImage
    orphaned_images = PostImage.objects.filter(post=instance)
    for post_image in orphaned_images:
        # The PostImage signal will handle file deletion
        post_image.delete()