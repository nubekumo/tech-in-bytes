from PIL import Image
import os
from django.core.files.base import ContentFile
from io import BytesIO


def process_avatar_image(image_field, size=(300, 300)):
    """
    Process and center crop the avatar image to ensure it fits properly in a circular container.
    
    Args:
        image_field: The uploaded image file
        size: Tuple of (width, height) for the final image size
    
    Returns:
        ContentFile: Processed image ready to be saved
    """
    if not image_field:
        return None
    
    try:
        # Open the image
        img = Image.open(image_field)

        # Detect if image has transparency
        has_alpha = (
            img.mode in ('RGBA', 'LA')
            or (img.mode == 'P' and 'transparency' in img.info)
        )

        # Normalize modes
        if has_alpha and img.mode != 'RGBA':
            img = img.convert('RGBA')
        if not has_alpha and img.mode != 'RGB':
            img = img.convert('RGB')

        # Get the current dimensions
        width, height = img.size

        # Center square crop
        if width > height:
            left = (width - height) // 2
            right = left + height
            top = 0
            bottom = height
        else:
            top = (height - width) // 2
            bottom = top + width
            left = 0
            right = width

        img = img.crop((left, top, right, bottom))
        img = img.resize(size, Image.Resampling.LANCZOS)

        # Choose output format based on alpha
        output_format = 'PNG' if has_alpha else 'JPEG'
        img_io = BytesIO()
        if output_format == 'PNG':
            img.save(img_io, format='PNG', optimize=True)
            new_ext = '.png'
        else:
            img.save(img_io, format='JPEG', quality=95, optimize=True)
            new_ext = '.jpg'
        img_io.seek(0)

        # Build a proper filename with the right extension
        base = os.path.splitext(os.path.basename(image_field.name))[0]
        filename = f"{base}{new_ext}"
        return ContentFile(img_io.getvalue(), name=filename)

    except Exception as e:
        # If processing fails, return None to use original image
        # Avatar processing failed (can be logged properly in production)
        return None


def process_avatar_image_with_focus(*args, **kwargs):
    """Deprecated: maintained for compatibility; delegates to process_avatar_image."""
    image_field = args[0] if args else kwargs.get('image_field')
    size = kwargs.get('size', (300, 300))
    return process_avatar_image(image_field, size=size)