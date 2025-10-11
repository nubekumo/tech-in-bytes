from PIL import Image
import os
from django.core.files.base import ContentFile
from io import BytesIO


def process_avatar_image(image_field, size=(300, 300), offset_x=0, offset_y=0):
    """
    Process and center crop the avatar image to ensure it fits properly in a circular container.
    
    Args:
        image_field: The uploaded image file
        size: Tuple of (width, height) for the final image size
        offset_x: Horizontal offset in pixels for user-defined centering
        offset_y: Vertical offset in pixels for user-defined centering
    
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

        # Calculate the square crop size (use the smaller dimension)
        crop_size = min(width, height)
        
        # Calculate scale factor for offsetting
        # offset values come from 250px preview, scale to actual image resolution
        scale_factor = crop_size / 250.0
        
        # Apply offset to center point (negate because drag right = crop left)
        scaled_offset_x = -int(offset_x * scale_factor)
        scaled_offset_y = -int(offset_y * scale_factor)

        # Calculate center point (middle of image + user offset)
        center_x = width // 2 + scaled_offset_x
        center_y = height // 2 + scaled_offset_y

        # Calculate square crop box
        half_crop = crop_size // 2
        left = center_x - half_crop
        top = center_y - half_crop
        right = left + crop_size
        bottom = top + crop_size

        # Ensure crop box stays within image bounds
        if left < 0:
            left = 0
            right = crop_size
        if top < 0:
            top = 0
            bottom = crop_size
        if right > width:
            right = width
            left = width - crop_size
        if bottom > height:
            bottom = height
            top = height - crop_size

        # Perform the crop
        img = img.crop((left, top, right, bottom))
        
        # Resize to final size
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