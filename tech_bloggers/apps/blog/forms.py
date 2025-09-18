from django import forms
from .models import Post, Tag


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        # Do not expose 'status' in the form; it is set via buttons (draft/publish)
        fields = ['title', 'content', 'summary', 'image', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your post title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your blog content here...'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write a short summary...'
            }),
            'image': forms.FileInput(attrs={
                'class': 'hidden-file-input',
                'accept': 'image/*'
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-control tag-select', 
                'multiple': True
            }),
        }
