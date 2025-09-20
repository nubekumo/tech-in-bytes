from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete
from django.dispatch import receiver
from PIL import Image
import os

def validate_image(image):
    # Check file size (2MB limit)
    if image.size > 2 * 1024 * 1024:  # 2MB
        raise ValidationError("Image too large. Max size is 2MB.")

    # Check image format (only JPEG, PNG, WebP allowed)
    try:
        with Image.open(image) as img:
            if img.format not in ["JPEG", "JPG", "PNG", "WEBP"]:
                raise ValidationError("Unsupported image format. Use JPEG, PNG, or WebP.")
    except Exception:
        raise ValidationError("Invalid image file.")
    

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    

class Post(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("published", "Published")]
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    summary = models.TextField(blank=True)
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
    

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created_at']
        indexes = [models.Index(fields=['created_at'])]

    def __str__(self):
        return f"Comment by {self.author} on {self.post}."


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