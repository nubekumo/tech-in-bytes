from django import forms
from django_summernote.widgets import SummernoteInplaceWidget
import bleach
import re
from django.conf import settings
from .models import Post, Tag


class PostForm(forms.ModelForm):
    # Custom tags field to handle the string input from our custom interface
    tags_input = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Comma-separated tag IDs"
    )

    class Meta:
        model = Post
        # Do not expose 'status' in the form; it is set via buttons (draft/publish)
        fields = ['title', 'content', 'summary', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your post title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your blog content here...',
                'id': 'id_content'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write a short summary...'
            }),
            'image': forms.FileInput(attrs={
                'class': 'hidden-file-input',
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add a custom field to pass available tags to template
        self.fields['available_tags'] = forms.ModelMultipleChoiceField(
            queryset=Tag.objects.all().order_by('name'),
            required=False,
            widget=forms.HiddenInput()
        )

        # If editing an existing post, populate the tags_input field
        if self.instance and self.instance.pk:
            tag_ids = list(self.instance.tags.values_list('id', flat=True))
            self.fields['tags_input'].initial = ','.join(map(str, tag_ids))

    def clean_tags_input(self):
        """Custom validation for tags input field"""
        tags_data = self.cleaned_data.get('tags_input', '')
        
        if tags_data.strip():
            tag_ids = [tag_id.strip() for tag_id in tags_data.split(',') if tag_id.strip()]
            # Convert string IDs to integers and validate they exist
            try:
                tag_ids = [int(tag_id) for tag_id in tag_ids]
                existing_tags = Tag.objects.filter(id__in=tag_ids)
                if len(existing_tags) != len(tag_ids):
                    raise forms.ValidationError("Some selected tags are invalid.")
                
                # Validate maximum 3 tags
                if len(existing_tags) > 3:
                    raise forms.ValidationError("You can select a maximum of 3 tags.")
                    
                return existing_tags
            except (ValueError, Tag.DoesNotExist):
                raise forms.ValidationError("Invalid tag selection.")
        else:
            return []

    def clean_content(self):
        """Sanitize content using bleach"""
        content = self.cleaned_data.get('content', '')
        if content:
            # Sanitize the HTML content
            sanitized_content = bleach.clean(
                content,
                tags=settings.BLEACH_ALLOWED_TAGS,
                attributes=settings.BLEACH_ALLOWED_ATTRIBUTES,
                css_sanitizer=bleach.css_sanitizer.CSSSanitizer(allowed_css_properties=settings.BLEACH_ALLOWED_STYLES),
                protocols=settings.BLEACH_ALLOWED_PROTOCOLS,
                strip_comments=True
            )
            
            # Remove empty font tags and other problematic tags
            # Remove empty font tags
            sanitized_content = re.sub(r'<font[^>]*>\s*</font>', '', sanitized_content)
            # Remove font tags that only contain whitespace or other empty font tags
            sanitized_content = re.sub(r'<font[^>]*>\s*(<font[^>]*>\s*</font>\s*)*</font>', '', sanitized_content)
            # Clean up any remaining empty tags
            sanitized_content = re.sub(r'<(\w+)[^>]*>\s*</\1>', '', sanitized_content)
            
            return sanitized_content
        return content

    def save(self, commit=True):
        """Override save to handle custom tags field and sanitize content"""
        instance = super().save(commit=False)
        
        # Sanitize content before saving
        if 'content' in self.cleaned_data:
            instance.content = self.cleaned_data['content']
        
        if commit:
            instance.save()
            # Set the tags using the cleaned tags_input data
            tags = self.cleaned_data.get('tags_input', [])
            instance.tags.set(tags)
            
            # Associate any orphaned PostImage records with this post
            from .models import PostImage
            if hasattr(self, 'user') and self.user:
                # Find PostImage records uploaded by this user that don't have a post
                orphaned_images = PostImage.objects.filter(
                    uploaded_by=self.user,
                    post__isnull=True
                )
                # Associate them with this post
                orphaned_images.update(post=instance)
            
        return instance


class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your name'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your email address'
    }))
    to = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': "Recipient's email address"
    }))
    comments = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control',
        'placeholder': 'Add a personal message (optional)',
        'rows': 4
    }))