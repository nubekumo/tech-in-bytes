# CloudFront Setup Guide for Tech-In-Bytes

This guide covers setting up AWS CloudFront in front of your EC2 instance for SSL/HTTPS termination and content delivery.

## Architecture Overview

```
User Browser
    ↓ (HTTPS - ACM Certificate)
CloudFront Distribution
    ↓ (HTTP - AWS internal network)
EC2 Instance (Nginx → Gunicorn → Django)
```

## Benefits of This Architecture

✅ **SSL/HTTPS handled by CloudFront** (using your ACM certificate)
✅ **No SSL certificate management on EC2** (no Let's Encrypt needed)
✅ **Better performance** with CloudFront CDN caching
✅ **DDoS protection** from CloudFront
✅ **Lower EC2 CPU usage** (no SSL processing)
✅ **Static/Media files served from S3** via CloudFront
✅ **Dynamic content cached** at edge locations

---

## Step-by-Step CloudFront Configuration

### 1. Create CloudFront Distribution

**Origin Settings:**
- **Origin Domain:** Your EC2 public IP or DNS (e.g., `ec2-xx-xx-xx-xx.compute.amazonaws.com`)
- **Protocol:** HTTP Only (port 80)
- **Origin Path:** Leave empty
- **Origin ID:** `EC2-Django-App`
- **Add custom header (recommended):**
  - Header name: `X-Origin-Verify`
  - Value: Generate a random string (e.g., `secure-random-token-123`)
  - This prevents direct access to EC2, forcing traffic through CloudFront

**Default Cache Behavior:**
- **Viewer Protocol Policy:** Redirect HTTP to HTTPS
- **Allowed HTTP Methods:** GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
- **Cache Policy:** Create custom or use `CachingDisabled` for dynamic content
- **Origin Request Policy:** `AllViewer` (forwards all headers, cookies, query strings)
- **Compress Objects Automatically:** Yes

**Settings:**
- **Alternate Domain Names (CNAMEs):** 
  - `tech-in-bytes.com`
  - `www.tech-in-bytes.com`
- **SSL Certificate:** Select your ACM certificate
- **Supported HTTP Versions:** HTTP/2, HTTP/3
- **Default Root Object:** Leave empty (Django handles routing)
- **Logging:** Enable (optional, for analytics)

### 2. Additional Cache Behaviors (for Static/Media from S3)

Create separate cache behaviors for static and media files:

**Cache Behavior #1 - Static Files:**
- **Path Pattern:** `/static/*`
- **Origin:** Your S3 static bucket
- **Cache Policy:** `CachingOptimized`
- **Compress Objects:** Yes
- **Viewer Protocol Policy:** Redirect HTTP to HTTPS

**Cache Behavior #2 - Media Files:**
- **Path Pattern:** `/media/*`
- **Origin:** Your S3 media bucket
- **Cache Policy:** `CachingOptimized`
- **Compress Objects:** Yes
- **Viewer Protocol Policy:** Redirect HTTP to HTTPS

**Priority order:** Static → Media → Default (EC2)

### 3. Route 53 DNS Configuration

Create DNS records pointing to CloudFront:

```
Type: A
Name: tech-in-bytes.com
Alias: Yes
Alias Target: Your CloudFront distribution (e.g., d1234abcd.cloudfront.net)

Type: A
Name: www.tech-in-bytes.com
Alias: Yes
Alias Target: Your CloudFront distribution (e.g., d1234abcd.cloudfront.net)
```

### 4. Security Headers (CloudFront Response Headers Policy)

Create a custom response headers policy:

**Security Headers:**
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

Apply this policy to your distribution's default cache behavior.

---

## EC2 Security Group Configuration

Update your EC2 security group to only accept traffic from CloudFront (optional but recommended):

**Inbound Rules:**
```
Type: SSH
Protocol: TCP
Port: 22
Source: Your IP address

Type: HTTP
Protocol: TCP
Port: 80
Source: CloudFront Prefix List (com.amazonaws.global.cloudfront.origin-facing)
OR
Source: 0.0.0.0/0 (if you want to test direct access)
```

**Note:** You can find CloudFront IP ranges at: https://d7uri8nf7uskq.cloudfront.net/tools/list-cloudfront-ips

---

## Django Configuration Updates

Your Django settings already handle this correctly:

**In `settings/production.py`:**
```python
# Trust CloudFront's forwarded protocol
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Set allowed hosts
ALLOWED_HOSTS = ['tech-in-bytes.com', 'www.tech-in-bytes.com']

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = ['https://tech-in-bytes.com', 'https://www.tech-in-bytes.com']
```

---

## Testing Your Setup

### 1. Test EC2 Directly (HTTP)
```bash
curl http://your-ec2-ip/health
# Should return: healthy
```

### 2. Test CloudFront (HTTPS)
```bash
curl -I https://tech-in-bytes.com
# Should show:
# - HTTP/2 200
# - CloudFront headers (x-amz-cf-id, x-cache)
# - Security headers
```

### 3. Test Static Files
```bash
curl -I https://tech-in-bytes.com/static/css/base.css
# Should show x-cache: Hit from cloudfront (after first request)
```

### 4. Check SSL Certificate
```bash
openssl s_client -connect tech-in-bytes.com:443 -servername tech-in-bytes.com | grep "subject"
# Should show your domain
```

### 5. Test in Browser
- Visit `https://tech-in-bytes.com`
- Check browser developer tools → Network tab
- Verify:
  - ✅ HTTPS padlock shows
  - ✅ Static/media files load from CloudFront
  - ✅ Pages load correctly
  - ✅ Forms submit successfully (CSRF works)

---

## Troubleshooting

### Issue: CloudFront returns 502 Bad Gateway

**Possible causes:**
1. EC2 instance is not running
2. Gunicorn is not running: `sudo systemctl status gunicorn`
3. Nginx is not running: `sudo systemctl status nginx`
4. Security group blocks CloudFront IP ranges
5. Origin domain is incorrect in CloudFront

**Solution:**
- Check EC2 health: `curl http://localhost/health`
- Check Gunicorn: `sudo journalctl -u gunicorn -n 50`
- Check Nginx: `sudo tail -f /var/log/nginx/techinbytes-error.log`

### Issue: CSRF verification failed

**Cause:** Django doesn't recognize the request as HTTPS

**Solution:**
- Verify `SECURE_PROXY_SSL_HEADER` is set in settings
- Check CloudFront forwards `X-Forwarded-Proto` header
- Ensure `CSRF_TRUSTED_ORIGINS` includes your domain with `https://`

### Issue: Static/Media files not loading

**Possible causes:**
1. S3 bucket permissions incorrect
2. CloudFront cache behavior path patterns wrong
3. Django STATIC_URL/MEDIA_URL pointing to wrong location

**Solution:**
- Verify S3 bucket policy allows CloudFront OAI
- Check CloudFront cache behaviors order (most specific first)
- Test direct S3 URLs to verify files uploaded correctly

### Issue: Slow initial page loads

**Expected behavior:** First request to CloudFront edge location is slower (cache miss)

**Solution:**
- After first request, subsequent requests will be fast (cache hit)
- Configure appropriate TTL in cache policies
- Use CloudFront invalidations sparingly (they cost money)

### Issue: Can't access Django admin

**Possible causes:**
1. Static files not loading (admin CSS/JS from S3)
2. HTTPS redirect causing issues
3. Cookie settings incorrect

**Solution:**
- Run `python manage.py collectstatic` and upload to S3
- Check browser console for errors
- Verify `SESSION_COOKIE_SECURE = True` in production settings

---

## CloudFront Cache Invalidation

When you deploy new static files or need to clear cache:

```bash
# Invalidate specific paths
aws cloudfront create-invalidation \
    --distribution-id YOUR_DISTRIBUTION_ID \
    --paths "/static/*" "/media/*"

# Invalidate everything (use sparingly, costs money)
aws cloudfront create-invalidation \
    --distribution-id YOUR_DISTRIBUTION_ID \
    --paths "/*"
```

**Note:** First 1,000 invalidation paths per month are free, then $0.005 per path.

---

## Cost Optimization Tips

1. **Set appropriate cache TTLs** - Don't cache dynamic content, do cache static/media
2. **Use S3 for static/media** - Much cheaper than serving from EC2
3. **Enable compression** - Reduces data transfer costs
4. **Choose the right price class** - If your users are regional, don't pay for worldwide edge locations
5. **Monitor usage** - Use CloudWatch to track requests and data transfer

---

## Monitoring

### CloudFront Metrics (CloudWatch)
- Requests
- Bytes Downloaded/Uploaded
- Error Rate (4xx, 5xx)
- Cache Hit Rate

### Set Up Alarms
```bash
# Example: Alert on high error rate
aws cloudwatch put-metric-alarm \
    --alarm-name cloudfront-high-errors \
    --alarm-description "Alert when CloudFront 5xx errors exceed threshold" \
    --metric-name 5xxErrorRate \
    --namespace AWS/CloudFront \
    --statistic Average \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold
```

---

## Next Steps

After CloudFront is configured:

1. ✅ Test thoroughly (use checklist above)
2. ✅ Monitor for 24-48 hours
3. ✅ Set up billing alerts
4. ✅ Document your specific configuration
5. ✅ Create runbook for common issues
6. ✅ Set up automated backups
7. ✅ Configure AWS CloudWatch alarms

---

## Additional Resources

- [CloudFront Developer Guide](https://docs.aws.amazon.com/cloudfront/)
- [CloudFront Pricing](https://aws.amazon.com/cloudfront/pricing/)
- [Django Behind a Proxy](https://docs.djangoproject.com/en/stable/ref/settings/#secure-proxy-ssl-header)
- [AWS CloudFront IP Ranges](https://d7uri8nf7uskq.cloudfront.net/tools/list-cloudfront-ips)


