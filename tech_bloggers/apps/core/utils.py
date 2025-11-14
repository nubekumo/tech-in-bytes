from typing import Any


def get_client_ip(request):
    """
    Return the left-most IP in the X-Forwarded-For header.
    Remove any trailing CIDR mask (e.g. '/64') CloudFront may append.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        for part in forwarded.split(','):
            ip = part.strip()
            if not ip:
                continue
            # strip mask if present
            if '/' in ip:
                ip = ip.split('/')[0]
            if ip:
                return ip
    remote = request.META.get("REMOTE_ADDR", "") or ""
    if '/' in remote:
        remote = remote.split('/')[0]
    return remote


def delete_stored_file(field_file: Any) -> bool:
    """
    Delete a Django FileField/ImageField file regardless of storage backend.

    Returns True if deletion was attempted, False otherwise.
    """
    if not field_file:
        return False

    file_name = getattr(field_file, "name", None)
    storage = getattr(field_file, "storage", None)

    if not file_name or not storage:
        return False

    try:
        # FieldFile.delete() already handles both storage deletion and
        # clearing the field value, but we disable model saving.
        field_file.delete(save=False)
        return True
    except NotImplementedError:
        try:
            storage.delete(file_name)
            return True
        except Exception:
            return False
    except (ValueError, OSError, AttributeError):
        try:
            storage.delete(file_name)
            return True
        except Exception:
            return False
