from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView,
    DeleteView, View, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.conf import settings
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import json
import uuid
from .models import Post, Comment, Tag, PostImage
from .forms import PostForm, EmailPostForm

class SlugRedirectMixin:
    """Mixin to handle slug redirects when slug in URL doesn't match current slug."""
    def get(self, request, *args, **kwargs):
        # Get post by pk first
        post = get_object_or_404(Post, pk=kwargs.get('pk'))
        # If slug doesn't match, redirect to the correct URL
        if post.slug != kwargs.get('slug'):
            return redirect(self.get_redirect_url(post))
        return super().get(request, *args, **kwargs)
    
    def get_redirect_url(self, post):
        """Get the correct URL for the post. Override in child classes."""
        raise NotImplementedError

class PostListView(ListView):
    model = Post
    template_name = 'blog/all_posts.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        queryset = Post.objects.filter(status='published').select_related('author')
        
        # Handle search query
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(summary__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()
        
        # Handle category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(tags__slug=category)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available tags for the filter dropdown
        context['available_tags'] = Tag.objects.all().order_by('name')
        
        # Get current search query and category for template
        context['current_search'] = self.request.GET.get('q', '')
        context['current_category'] = self.request.GET.get('category', '')
        
        # Get current tag if filtering by category
        if context['current_category']:
            try:
                context['current_tag'] = Tag.objects.get(slug=context['current_category'])
            except Tag.DoesNotExist:
                context['current_tag'] = None
        else:
            context['current_tag'] = None
            
        return context


class LikedPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'blog/liked_posts.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.objects.filter(
            likes=self.request.user,
            status='published'
        ).select_related('author').prefetch_related('tags')
        
        # Handle category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(tags__slug=category)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available tags for the filter dropdown
        context['available_tags'] = Tag.objects.all().order_by('name')
        
        # Get current category for template
        context['current_category'] = self.request.GET.get('category', '')
        
        # Get current tag if filtering by category
        if context['current_category']:
            try:
                context['current_tag'] = Tag.objects.get(slug=context['current_category'])
            except Tag.DoesNotExist:
                context['current_tag'] = None
        else:
            context['current_tag'] = None
            
        return context


class PostDetailView(SlugRedirectMixin, DetailView):
    model = Post
    template_name = 'blog/single_post.html'
    context_object_name = 'post'
    
    def get_redirect_url(self, post):
        return reverse('blog:post_detail', kwargs={'pk': post.pk, 'slug': post.slug})

    def get_queryset(self):
        return super().get_queryset().select_related('author').prefetch_related(
            'tags',
            'comments__author',
            'comments__replies__author'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = context['post']
        # Add top-level comments to context
        context['top_level_comments'] = post.comments.filter(parent__isnull=True)
        return context

@method_decorator(ratelimit(key='user', rate='2/m', method='POST', block=True), name='dispatch')
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create_post.html'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_form(self, form_class=None):
        """Override to set user on form after creation"""
        form = super().get_form(form_class)
        form.user = self.request.user
        return form

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.user = self.request.user  # Pass user to form for PostImage association
        
        # Check which button was clicked
        action = self.request.POST.get('action')
        
        if action == 'draft':
            form.instance.status = 'draft'
        elif action == 'publish':
            form.instance.status = 'published'
            from django.utils import timezone
            form.instance.published_at = timezone.now()
        
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('blog:post_manage')

class PostManageView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'blog/manage_posts.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.objects.filter(author=self.request.user).select_related('author')
        
        # Handle search query
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            ).distinct()
        
        # Handle status filter
        status = self.request.GET.get('status')
        if status in ['published', 'draft']:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current search query and status for template
        context['current_search'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        
        return context

@method_decorator(ratelimit(key='user', rate='10/m', method='POST', block=True), name='dispatch')
class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, SlugRedirectMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/edit_post.html'

    def get_object(self, queryset=None):
        """Override to cache the object and avoid multiple queries."""
        if not hasattr(self, '_object'):
            self._object = super().get_object(queryset)
        return self._object

    def test_func(self):
        post = self.get_object()  # Uses cached object
        return self.request.user == post.author

    def get_redirect_url(self, post):
        return reverse('blog:post_edit', kwargs={'pk': post.pk, 'slug': post.slug})

    def get_success_url(self):
        return reverse('blog:post_manage')

    def get_form(self, form_class=None):
        """Override to set user on form after creation"""
        form = super().get_form(form_class)
        form.user = self.request.user
        return form

    def form_valid(self, form):
        """Override form_valid to add success message after update."""
        form.user = self.request.user  # Pass user to form for PostImage association
        messages.success(self.request, 'Your post has been updated successfully')
        return super().form_valid(form)

@method_decorator(ratelimit(key='user', rate='2/m', method='POST', block=True), name='dispatch')
class PostPublishView(LoginRequiredMixin, UserPassesTestMixin, SlugRedirectMixin, UpdateView):
    model = Post
    template_name = 'blog/publish_post.html'
    fields = []  # No form fields needed, we're just changing status

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_redirect_url(self, post):
        return reverse('blog:post_publish', kwargs={'pk': post.pk, 'slug': post.slug})

    def get_success_url(self):
        return reverse('blog:post_manage')

    def post(self, request, *args, **kwargs):
        """Override post method to toggle publish status and add success message."""
        post = self.get_object()
        
        # Toggle the status
        if post.status == 'draft':
            post.status = 'published'
            from django.utils import timezone
            post.published_at = timezone.now()
            success_message = 'Your post has been published'
        else:
            post.status = 'draft'
            success_message = 'Your post has been unpublished'
        
        post.save()
        messages.success(request, success_message)
        
        return redirect(self.get_success_url())

@method_decorator(ratelimit(key='user', rate='2/m', method='POST', block=True), name='dispatch')
class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, SlugRedirectMixin, DeleteView):
    model = Post
    template_name = 'blog/delete_post.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_redirect_url(self, post):
        return reverse('blog:post_delete', kwargs={'pk': post.pk, 'slug': post.slug})

    def get_success_url(self):
        return reverse('blog:post_manage')

    def post(self, request, *args, **kwargs):
        """Override post method to add success message before deletion."""
        messages.success(request, 'Your post has been deleted')
        return super().post(request, *args, **kwargs)

@method_decorator(ratelimit(key='user', rate='10/m', method='POST', block=True), name='dispatch')
class PostLikeView(LoginRequiredMixin, View):
    def post(self, request, pk, slug):
        post = get_object_or_404(Post, pk=pk)
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        
        # Return JSON response for AJAX requests
        return JsonResponse({
            'liked': liked, 
            'count': post.likes.count(),
            'status': 'success'
        })

@method_decorator(ratelimit(key='user', rate='10/m', method='POST', block=True), name='dispatch')
class PostRecommendView(LoginRequiredMixin, View):
    def post(self, request, pk, slug):
        post = get_object_or_404(Post, pk=pk)
        # In MVP, just log to console
        # Recommendation logged (can be removed in production)
        messages.success(request, "Post recommendation logged (MVP)")
        return JsonResponse({'status': 'success'})

@method_decorator(ratelimit(key='user', rate='3/m', method='POST', block=True), name='dispatch')
class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs.get('pk'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={
            'pk': self.kwargs.get('pk'),
            'slug': self.kwargs.get('slug')
        })

@method_decorator(ratelimit(key='user', rate='3/m', method='POST', block=True), name='dispatch')
class CommentReplyView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['content']

    def form_valid(self, form):
        parent_comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        form.instance.author = self.request.user
        form.instance.post = parent_comment.post
        form.instance.parent = parent_comment
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={
            'pk': self.object.post.pk,
            'slug': self.object.post.slug
        })


@method_decorator(csrf_protect, name='dispatch')
@method_decorator(ratelimit(key='user', rate='10/m', method='POST', block=True), name='dispatch')
class ImageUploadView(LoginRequiredMixin, View):
    """
    Handle image uploads from TinyMCE editor
    """
    def post(self, request):
        try:
            # Get the uploaded file
            if 'file' not in request.FILES:
                return JsonResponse({'error': 'No file provided'}, status=400)
            
            uploaded_file = request.FILES['file']

            # Check user's image quota limits
            user_image_count = PostImage.get_user_image_count(request.user)
            max_images_per_user = getattr(settings, 'MAX_IMAGES_PER_USER', 200)
            if user_image_count >= max_images_per_user:
                return JsonResponse({
                    'error': f'Image limit reached. You can upload a maximum of {max_images_per_user} images.'
                }, status=400)

            # Check user's storage quota
            user_storage_mb = PostImage.get_user_storage_mb(request.user)
            max_storage_mb = getattr(settings, 'MAX_STORAGE_PER_USER_MB', 400)
            if user_storage_mb >= max_storage_mb:
                return JsonResponse({
                    'error': f'Storage limit reached. You have used {user_storage_mb}MB of {max_storage_mb}MB allowed.'
                }, status=400)

            # Check if this upload would exceed storage limit
            max_bytes = getattr(settings, 'IMAGE_MAX_UPLOAD_MB', 2) * 1024 * 1024
            if uploaded_file.size and uploaded_file.size > max_bytes:
                return JsonResponse({'error': f'File too large. Maximum size is {getattr(settings, "IMAGE_MAX_UPLOAD_MB", 2)}MB.'}, status=400)
            
            # Check if this upload would exceed user's storage quota
            file_size_mb = uploaded_file.size / (1024 * 1024) if uploaded_file.size else 0
            if user_storage_mb + file_size_mb > max_storage_mb:
                return JsonResponse({
                    'error': f'Upload would exceed storage limit. You have {max_storage_mb - user_storage_mb:.1f}MB remaining.'
                }, status=400)

            # Process and sanitize image: validate, resize, strip EXIF, re-encode
            try:
                Image.MAX_IMAGE_PIXELS = getattr(settings, 'IMAGE_MAX_PIXELS', 12000000)
                with Image.open(uploaded_file) as img:
                    original_format = (img.format or '').upper()
                    allowed_formats = {"JPEG", "JPG", "PNG", "WEBP"}
                    target_format = original_format if original_format in allowed_formats else "PNG"

                    # Convert mode for JPEG (no alpha)
                    if target_format in {"JPEG", "JPG"} and img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    # Enforce dimension limits by downscaling if necessary
                    max_w = getattr(settings, 'IMAGE_MAX_WIDTH', 2048)
                    max_h = getattr(settings, 'IMAGE_MAX_HEIGHT', 2048)
                    width, height = img.size
                    if width > max_w or height > max_h:
                        img.thumbnail((max_w, max_h))

                    # Re-encode without EXIF/metadata
                    buffer = BytesIO()
                    save_kwargs = {}
                    if target_format in {"JPEG", "JPG"}:
                        target_format = "JPEG"
                        save_kwargs.update({"quality": 85, "optimize": True})
                    elif target_format == "PNG":
                        save_kwargs.update({"optimize": True})
                    elif target_format == "WEBP":
                        save_kwargs.update({"quality": 85, "method": 6})

                    img.save(buffer, format=target_format, **save_kwargs)
                    buffer.seek(0)

            except UnidentifiedImageError:
                return JsonResponse({'error': 'Invalid image file.'}, status=400)
            except Exception as e:
                return JsonResponse({'error': f'Image processing failed: {str(e)}'}, status=400)

            # Choose extension based on target format
            ext_map = {"JPEG": "jpg", "JPG": "jpg", "PNG": "png", "WEBP": "webp"}
            extension = ext_map.get(target_format, 'png')
            unique_filename = f"{uuid.uuid4().hex}.{extension}"

            # Save file to media/post_images/content/
            file_path = f"post_images/content/{unique_filename}"
            saved_path = default_storage.save(file_path, ContentFile(buffer.getvalue()))

            # Get the full URL for the saved file
            file_url = request.build_absolute_uri(default_storage.url(saved_path))
            
            # Create a PostImage record to track the uploaded image
            # We'll associate it with a temporary post or handle it in the workflow
            # For now, we'll create it without a post association (post can be None)
            # Per-post image limit will be enforced in the form validation
            post_image = PostImage.objects.create(
                post=None,  # Will be associated when the post is saved
                image=saved_path,
                uploaded_by=request.user,
                original_filename=uploaded_file.name
            )
            
            # Return the URL in TinyMCE expected format
            return JsonResponse({
                'location': file_url
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Upload failed: {str(e)}'}, status=500)


@method_decorator(csrf_protect, name='dispatch')
class ImageDeleteView(LoginRequiredMixin, View):
    """
    Handle image deletion when user cancels TinyMCE dialog
    """
    def post(self, request):
        try:
            import json
            data = json.loads(request.body)
            image_url = data.get('url')
            
            if not image_url:
                return JsonResponse({'error': 'No image URL provided'}, status=400)
            
            # Extract filename from URL
            filename = image_url.split('/')[-1]
            file_path = f"post_images/content/{filename}"
            
            # Delete PostImage records referencing this file (which will also delete the underlying file)
            deleted = False
            post_images = PostImage.objects.filter(image__endswith=filename)
            if post_images.exists():
                post_images.delete()
                deleted = True

            # If no PostImage record exists (e.g., orphaned upload), delete via storage directly
            if not deleted and default_storage.exists(file_path):
                default_storage.delete(file_path)
                deleted = True

            if deleted:
                return JsonResponse({'success': True, 'message': f'Deleted {filename}'})

            return JsonResponse({'error': 'File not found'}, status=404)
                
        except Exception as e:
            return JsonResponse({'error': f'Delete failed: {str(e)}'}, status=500)


class PostShareView(View):
    template_name = 'blog/share_post.html'

    def get(self, request, pk, slug):
        post = get_object_or_404(Post, pk=pk)
        # Ensure correct slug in URL
        if post.slug != slug:
            return redirect(reverse('blog:post_share', kwargs={'pk': post.pk, 'slug': post.slug}))

        form = EmailPostForm()
        return render(request, self.template_name, {
            'post': post,
            'form': form,
            'sent': False,
        })

    def post(self, request, pk, slug):
        post = get_object_or_404(Post, pk=pk)
        # Ensure correct slug in URL
        if post.slug != slug:
            return redirect(reverse('blog:post_share', kwargs={'pk': post.pk, 'slug': post.slug}))

        form = EmailPostForm(request.POST)
        sent = False

        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(
                reverse('blog:post_detail', kwargs={'pk': post.pk, 'slug': post.slug})
            )

            subject = f"{cd['name']} recommends you read: {post.title}"
            message = (
                f"Hello,\n\n"
                f"{cd['name']} ({cd['email']}) thought you might be interested in this post:\n"
                f"{post.title}\n{post_url}\n\n"
                f"Comments by {cd['name']}: {cd.get('comments') or '—'}\n\n"
                f"Sent from Tech-In-Bytes"
            )

            email = EmailMessage(
                subject=subject,
                body=message,
                to=[cd['to']],
            )
            email.send()
            sent = True
            messages.success(request, 'E-mail successfully sent')

        return render(request, self.template_name, {
            'post': post,
            'form': form,
            'sent': sent,
        })