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
