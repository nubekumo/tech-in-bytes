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
from .models import Post, Comment
from taggit.models import Tag

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
        return Post.objects.filter(status='published').select_related('author')

class PostSearchView(ListView):
    model = Post
    template_name = 'blog/search_results.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            return Post.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(tags__name__icontains=query),
                status='published'
            ).distinct().select_related('author')
        return Post.objects.none()

class PostDetailView(SlugRedirectMixin, DetailView):
    model = Post
    template_name = 'blog/single_post.html'
    context_object_name = 'post'
    
    def get_redirect_url(self, post):
        return reverse('blog:post_detail', kwargs={'pk': post.pk, 'slug': post.slug})

    def get_queryset(self):
        return super().get_queryset().select_related('author').prefetch_related('tags')

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create_post.html'
    fields = ['title', 'content', 'summary', 'image', 'tags', 'status']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.pk, 'slug': self.object.slug})

class PostManageView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'blog/manage_posts.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).order_by('-created_at')

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, SlugRedirectMixin, UpdateView):
    model = Post
    template_name = 'blog/edit_post.html'
    fields = ['title', 'content', 'summary', 'image', 'tags', 'status']

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_redirect_url(self, post):
        return reverse('blog:post_edit', kwargs={'pk': post.pk, 'slug': post.slug})

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.pk, 'slug': self.object.slug})

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, SlugRedirectMixin, DeleteView):
    model = Post
    template_name = 'blog/delete_post.html'
    success_url = reverse_lazy('blog:post_manage')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_redirect_url(self, post):
        return reverse('blog:post_delete', kwargs={'pk': post.pk, 'slug': post.slug})

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
        return JsonResponse({'liked': liked, 'count': post.likes.count()})

class PostRecommendView(LoginRequiredMixin, View):
    def post(self, request, pk, slug):
        post = get_object_or_404(Post, pk=pk)
        # In MVP, just log to console
        print(f"Recommendation: User {request.user} recommends post {post.title}")
        messages.success(request, "Post recommendation logged (MVP)")
        return JsonResponse({'status': 'success'})

class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['content']
    template_name = 'blog/add_comment.html'

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
    template_name = 'blog/add_comment.html'

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