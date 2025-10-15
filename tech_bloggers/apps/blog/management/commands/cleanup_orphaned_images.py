from django.core.management.base import BaseCommand
from django.conf import settings
from apps.blog.models import PostImage


class Command(BaseCommand):
    help = 'Clean up orphaned images that are not associated with any post'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=getattr(settings, 'ORPHANED_IMAGE_CLEANUP_HOURS', 24),
            help='Number of hours after which orphaned images should be deleted (default: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        
        # Get orphaned images
        orphaned_images = PostImage.get_orphaned_images(hours)
        count = orphaned_images.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'No orphaned images found older than {hours} hours.')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would delete {count} orphaned images:')
            )
            for img in orphaned_images:
                self.stdout.write(f'  - {img.original_filename} (uploaded by {img.uploaded_by.username})')
            return
        
        # Delete orphaned images
        deleted_count = PostImage.cleanup_orphaned_images(hours)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} orphaned images.')
        )
