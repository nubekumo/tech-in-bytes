from django import template
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.conf import settings
import bleach
import re
import html

register = template.Library()

@register.filter
def safe_truncatewords(value, arg):
    """
    Safely truncate HTML content to a specified number of words.
    First sanitizes the HTML, then strips tags, decodes HTML entities, then truncates.
    """
    if not value:
        return ""
    
    # Sanitize the HTML content first
    sanitized = bleach.clean(
        value,
        tags=settings.BLEACH_ALLOWED_TAGS,
        attributes=settings.BLEACH_ALLOWED_ATTRIBUTES,
        css_sanitizer=bleach.css_sanitizer.CSSSanitizer(allowed_css_properties=settings.BLEACH_ALLOWED_STYLES),
        protocols=settings.BLEACH_ALLOWED_PROTOCOLS,
        strip_comments=True
    )
    
    # Strip HTML tags for word counting and display
    text_content = strip_tags(sanitized)
    
    # Decode HTML entities (e.g., &rsquo; -> ', &amp; -> &, etc.)
    text_content = html.unescape(text_content)
    
    # Split into words and truncate
    words = text_content.split()
    if len(words) <= int(arg):
        # If content is short enough, return the plain text (no HTML)
        return text_content
    
    # Truncate and add ellipsis
    truncated_words = words[:int(arg)]
    truncated_text = ' '.join(truncated_words) + '...'
    
    # Return as plain text (not mark_safe) to avoid HTML display issues
    return truncated_text

@register.filter
def striptags_unescape(value):
    """
    Strip HTML tags and decode HTML entities.
    Useful for displaying plain text from HTML content.
    """
    if not value:
        return ""
    
    # Strip HTML tags
    text_content = strip_tags(value)
    
    # Decode HTML entities (e.g., &rsquo; -> ', &amp; -> &, etc.)
    text_content = html.unescape(text_content)
    
    return text_content


@register.filter
def safe_content(value):
    """
    Safely render HTML content by sanitizing it with bleach.
    """
    if not value:
        return ""
    
    # Use normal sanitization (secure)
    sanitized = bleach.clean(
        value,
        tags=settings.BLEACH_ALLOWED_TAGS,
        attributes=settings.BLEACH_ALLOWED_ATTRIBUTES,
        css_sanitizer=bleach.css_sanitizer.CSSSanitizer(allowed_css_properties=settings.BLEACH_ALLOWED_STYLES),
        protocols=settings.BLEACH_ALLOWED_PROTOCOLS,
        strip_comments=True
    )
    
    # Remove empty font tags and other problematic tags
    # Remove empty font tags
    sanitized = re.sub(r'<font[^>]*>\s*</font>', '', sanitized)
    # Remove font tags that only contain whitespace or other empty font tags
    sanitized = re.sub(r'<font[^>]*>\s*(<font[^>]*>\s*</font>\s*)*</font>', '', sanitized)
    # Clean up empty tags but preserve empty paragraphs (needed for table spacing)
    # Remove empty spans, divs, strongs, ems, but keep empty <p> tags
    sanitized = re.sub(r'<(span|div|strong|em|b|i|u)[^>]*>\s*</\1>', '', sanitized)
    
    return mark_safe(sanitized)

