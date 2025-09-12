from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import models
from apps.blog.models import Post
from apps.blog.models import Tag
from .forms import ContactForm

class IndexView(TemplateView):
    template_name = "pages/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Base queryset for published posts
        published_posts = Post.objects.filter(
            status='published'
        ).select_related('author').prefetch_related('tags', 'comments')

        # Get latest 4 posts
        context['latest_posts'] = published_posts.order_by(
            '-published_at'
        )[:4]
        latest_ids = list(context['latest_posts'].values_list('id', flat=True))
        
        # Get 2 recently posted (excluding latest)
        context['recently_posted'] = published_posts.exclude(
            id__in=latest_ids
        ).order_by('-published_at')[:2]
        recently_posted_ids = list(context['recently_posted'].values_list('id', flat=True))
        
        # Get 2 most commented posts
        context['most_commented'] = published_posts.annotate(
            comment_count=models.Count('comments')
        ).order_by('-comment_count')[:2]
        most_commented_ids = list(context['most_commented'].values_list('id', flat=True))
        
        # Get 4 recommended posts (next 4 latest posts after 'latest_posts',
        # excluding most commented)
        excluded_ids = latest_ids + recently_posted_ids + most_commented_ids
        context['recommended_posts'] = published_posts.exclude(
            id__in=excluded_ids
        ).order_by('-published_at')[:4]
        
        # Get popular tags
        context['popular_tags'] = Tag.objects.annotate(
            post_count=models.Count('post')
        ).order_by('-post_count')[:10]

        return context

class AboutView(TemplateView):
    template_name = "pages/about.html"

class ContactView(FormView):
    template_name = "pages/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy('pages:contact')

    def form_valid(self, form):
        # For MVP, just print to console
        print(f"Contact Form Submission:")
        print(f" First Name: {form.cleaned_data['firstName']}")
        print(f" Last Name: {form.cleaned_data['lastName']}")
        print(f"Email: {form.cleaned_data['email']}")
        print(f"Subject: {form.cleaned_data['subject']}")
        print(f"Message: {form.cleaned_data['message']}")
        
        messages.success(
            self.request,
            "Thank you for your message! We'll get back to you soon. (MVP: Message logged to console)"
        )
        return super().form_valid(form)