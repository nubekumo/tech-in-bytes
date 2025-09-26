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
    paginate_by = 10

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

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create_post.html'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

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
        return Post.objects.filter(author=self.request.user).order_by('-created_at')

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

    def form_valid(self, form):
        """Override form_valid to add success message after update."""
        form.user = self.request.user  # Pass user to form for PostImage association
        messages.success(self.request, 'Your post has been updated successfully')
        return super().form_valid(form)

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

class TagListView(ListView):
    model = Tag
    template_name = 'blog/tag_list.html'
    context_object_name = 'tags'

class TaggedPostListView(ListView):
    model = Post
    template_name = 'blog/tagged_posts.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        tag_slug = self.kwargs.get('tag_slug')
        return Post.objects.filter(
            tags__slug=tag_slug,
            status='published'
        ).select_related('author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = get_object_or_404(Tag, slug=self.kwargs.get('tag_slug'))
        return context

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

class PostRecommendView(LoginRequiredMixin, View):
    def post(self, request, pk, slug):
        post = get_object_or_404(Post, pk=pk)
        # In MVP, just log to console
        # Recommendation logged (can be removed in production)
        messages.success(request, "Post recommendation logged (MVP)")
        return JsonResponse({'status': 'success'})

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
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if uploaded_file.content_type not in allowed_types:
                return JsonResponse({'error': 'Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.'}, status=400)
            
            # Validate file size (2MB limit)
            if uploaded_file.size > 2 * 1024 * 1024:
                return JsonResponse({'error': 'File too large. Maximum size is 2MB.'}, status=400)
            
            # Generate unique filename to avoid conflicts
            file_extension = uploaded_file.name.split('.')[-1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            # Save file to media/post_images/content/
            file_path = f"post_images/content/{unique_filename}"
            saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
            
            # Get the full URL for the saved file
            file_url = request.build_absolute_uri(default_storage.url(saved_path))
            
            # Create a PostImage record to track the uploaded image
            # We'll associate it with a temporary post or handle it in the workflow
            # For now, we'll create it without a post association (post can be None)
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
            
            # Delete the file
            if default_storage.exists(file_path):
                default_storage.delete(file_path)
                return JsonResponse({'success': True, 'message': f'Deleted {filename}'})
            else:
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
                f"Sent from Tech Bloggers"
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