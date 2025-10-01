from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
import os


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True, null=True, max_length=500, help_text="Tell us about yourself")

    def __str__(self):
        return self.user.username

    def delete(self, *args, **kwargs):
        # Delete the avatar file before deleting the profile
        self.delete_avatar()
        super().delete(*args, **kwargs)

    def delete_avatar(self, save=True):
        """Helper method to delete the avatar file and clear the field"""
        if self.avatar:
            try:
                if os.path.isfile(self.avatar.path):
                    os.remove(self.avatar.path)
            except (ValueError, OSError):
                # Handle cases where the file might not exist or path is invalid
                pass
            # Clear the field without triggering signals
            self.avatar = None
            if save:
                self.save(update_fields=['avatar'])


@receiver(pre_save, sender=Profile)
def delete_old_avatar(sender, instance, **kwargs):
    """Delete the old avatar file when a new one is uploaded"""
    if instance.pk:  # Only for existing profiles
        try:
            old_profile = Profile.objects.get(pk=instance.pk)
            if old_profile.avatar and old_profile.avatar != instance.avatar:
                # Delete the old avatar file directly
                try:
                    if os.path.isfile(old_profile.avatar.path):
                        os.remove(old_profile.avatar.path)
                except (ValueError, OSError):
                    pass
        except Profile.DoesNotExist:
            pass


@receiver(post_delete, sender=Profile)
def delete_avatar_file(sender, instance, **kwargs):
    """Delete the avatar file when the profile is deleted"""
    instance.delete_avatar(save=False)


@receiver(post_delete, sender=User)
def delete_user_avatar(sender, instance, **kwargs):
    """Delete the avatar file when the user is deleted"""
    try:
        if instance.profile:  # Access the profile before it's deleted
            instance.profile.delete_avatar(save=False)
    except Profile.DoesNotExist:
        pass