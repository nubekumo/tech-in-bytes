"""
Custom storage backends for AWS S3.
"""

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Custom storage class for media files (user uploads).
    Stores files in a separate 'media' folder in the S3 bucket.
    """
    location = settings.AWS_MEDIA_LOCATION
    file_overwrite = False
    default_acl = 'public-read'  # Media files should be publicly accessible

