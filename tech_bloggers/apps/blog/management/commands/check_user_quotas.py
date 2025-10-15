from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from apps.blog.models import PostImage


class Command(BaseCommand):
    help = 'Check user image upload quotas and storage usage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Check quota for specific user (username)'
        )
        parser.add_argument(
            '--show-all',
            action='store_true',
            help='Show quota information for all users with uploaded images'
        )

    def handle(self, *args, **options):
        max_images = getattr(settings, 'MAX_IMAGES_PER_USER', 200)
        max_storage = getattr(settings, 'MAX_STORAGE_PER_USER_MB', 400)
        
        if options['user']:
            try:
                user = User.objects.get(username=options['user'])
                self._show_user_quota(user, max_images, max_storage)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{options["user"]}" not found.')
                )
        elif options['show_all']:
            # Show all users with uploaded images
            users_with_images = User.objects.filter(
                postimage__isnull=False
            ).distinct().order_by('username')
            
            if not users_with_images:
                self.stdout.write(
                    self.style.SUCCESS('No users have uploaded images.')
                )
                return
            
            self.stdout.write(f'{"Username":<20} {"Images":<8} {"Storage":<12} {"% Used":<8} {"Status"}')
            self.stdout.write('-' * 70)
            
            for user in users_with_images:
                image_count = PostImage.get_user_image_count(user)
                storage_mb = PostImage.get_user_storage_mb(user)
                storage_percent = (storage_mb / max_storage) * 100 if max_storage > 0 else 0
                
                status = "OK"
                if image_count >= max_images or storage_mb >= max_storage:
                    status = "LIMIT REACHED"
                
                self.stdout.write(
                    f'{user.username:<20} {image_count:<8} {storage_mb:>8.1f}MB {storage_percent:>6.1f}% {status}'
                )
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --user <username> or --show-all')
            )

    def _show_user_quota(self, user, max_images, max_storage):
        """Show detailed quota information for a specific user"""
        image_count = PostImage.get_user_image_count(user)
        storage_mb = PostImage.get_user_storage_mb(user)
        
        image_percent = (image_count / max_images) * 100 if max_images > 0 else 0
        storage_percent = (storage_mb / max_storage) * 100 if max_storage > 0 else 0
        
        self.stdout.write(f'\nQuota Information for user: {user.username}')
        self.stdout.write('=' * 50)
        self.stdout.write(f'Images: {image_count}/{max_images} ({image_percent:.1f}%)')
        self.stdout.write(f'Storage: {storage_mb:.1f}/{max_storage}MB ({storage_percent:.1f}%)')
        
        # Show status
        if image_count >= max_images:
            self.stdout.write(self.style.ERROR('⚠️  IMAGE LIMIT REACHED'))
        if storage_mb >= max_storage:
            self.stdout.write(self.style.ERROR('⚠️  STORAGE LIMIT REACHED'))
        
        if image_count < max_images and storage_mb < max_storage:
            self.stdout.write(self.style.SUCCESS('✅ Quota OK'))
        
        # Show recent uploads
        recent_images = PostImage.objects.filter(
            uploaded_by=user
        ).order_by('-uploaded_at')[:5]
        
        if recent_images:
            self.stdout.write(f'\nRecent uploads:')
            for img in recent_images:
                status = "Associated" if img.post else "Orphaned"
                self.stdout.write(f'  - {img.original_filename} ({img.get_file_size_mb():.1f}MB) - {status}')
