# Security Features Manual Testing Checklist

## 🚀 Quick Start
1. Start your Django server: `python manage.py runserver`
2. Open browser and go to: `http://127.0.0.1:8000`
3. Open Developer Tools (F12) → Console tab
4. Follow this checklist

## ✅ Rate Limiting Tests

### Authentication Rate Limiting
- [ ] **Login Rate Limiting (10/min)**
  - Go to login page
  - Try wrong password 12 times quickly
  - Should be blocked after 10 attempts
  - ✅ Expected: Rate limit error after 10 attempts

- [ ] **Signup Rate Limiting (5/min)**
  - Go to signup page
  - Try creating accounts 7 times quickly
  - Should be blocked after 5 attempts
  - ✅ Expected: Rate limit error after 5 attempts

- [ ] **Password Reset Rate Limiting (5/min)**
  - Go to password reset page
  - Try password reset 7 times quickly
  - Should be blocked after 5 attempts
  - ✅ Expected: Rate limit error after 5 attempts

### Blog Action Rate Limiting (Login Required)
- [ ] **Post Creation Rate Limiting (2/min)**
  - Login to your account
  - Go to create post page
  - Try creating 4 posts in 1 minute
  - Should be limited to 2 per minute
  - ✅ Expected: Rate limit error after 2 attempts

- [ ] **Comment Rate Limiting (3/min)**
  - Go to any post
  - Try posting 5 comments in 1 minute
  - Should be limited to 3 per minute
  - ✅ Expected: Rate limit error after 3 attempts

- [ ] **Like Rate Limiting (10/min)**
  - Try liking 12 posts in 1 minute
  - Should be limited to 10 per minute
  - ✅ Expected: Rate limit error after 10 attempts

## ✅ File Upload Security Tests

### Image Upload Validation
- [ ] **Valid Image Upload**
  - Go to create post page
  - Upload a small JPEG/PNG image (<2MB)
  - Should work normally
  - ✅ Expected: Image uploads successfully

- [ ] **Large File Rejection**
  - Try uploading an image >2MB
  - Should be rejected with error message
  - ✅ Expected: "Image too large" error

- [ ] **Invalid File Type Rejection**
  - Try uploading a .txt, .pdf, or .exe file
  - Should be rejected with error message
  - ✅ Expected: "Unsupported image format" error

- [ ] **Oversized Dimensions**
  - Try uploading an image >2048x2048 pixels
  - Should be resized automatically
  - ✅ Expected: Image is resized and uploaded

### Image Processing
- [ ] **EXIF Data Stripping**
  - Upload an image with EXIF data (GPS, camera info)
  - Check if EXIF is removed in the uploaded image
  - ✅ Expected: EXIF data is stripped

## ✅ Content Security Policy (CSP) Tests

### CSP Header Verification
- [ ] **CSP Headers Present**
  - Open Developer Tools (F12)
  - Go to Network tab
  - Reload any page
  - Look for `Content-Security-Policy` or `Content-Security-Policy-Report-Only` headers
  - ✅ Expected: CSP headers are present

### Functionality Tests
- [ ] **Font Awesome Icons**
  - Check if all icons display correctly
  - Look for missing icons (broken image icons)
  - ✅ Expected: All icons display properly

- [ ] **TinyMCE Editor**
  - Go to create/edit post page
  - Check if rich text editor loads
  - Try using formatting tools
  - ✅ Expected: TinyMCE editor works fully

- [ ] **External Resources**
  - Check if external CSS/JS loads
  - Look for blocked requests in Network tab
  - ✅ Expected: All necessary resources load

### CSP Violations Check
- [ ] **Console Violations**
  - Open Console tab in Developer Tools
  - Visit all pages (home, login, create post, etc.)
  - Look for CSP violation messages
  - ✅ Expected: No CSP violations (or only expected ones)

## ✅ Overall Functionality Tests

### Navigation
- [ ] **All Pages Load**
  - Home page
  - Login page
  - Signup page
  - Blog list page
  - Create post page
  - Settings page
  - ✅ Expected: All pages load without errors

### Forms
- [ ] **Form Submissions Work**
  - Login form
  - Signup form
  - Create post form
  - Comment form
  - Settings form
  - ✅ Expected: All forms submit correctly

### User Experience
- [ ] **No Broken Features**
  - All buttons work
  - All links work
  - All forms function
  - All uploads work
  - ✅ Expected: Everything works as expected

## 🐛 Troubleshooting

### If Rate Limiting Doesn't Work:
- Check if django-ratelimit is properly installed
- Verify import statements in views.py
- Check Django cache configuration

### If File Upload Issues:
- Check image validation settings in settings.py
- Verify PIL/Pillow installation
- Check file size and format limits

### If CSP Issues:
- Check CSP configuration in settings.py
- Verify external domain whitelisting
- Check browser console for specific violations

### If Icons Missing:
- Check Font Awesome CDN in templates
- Verify CSP allows cdnjs.cloudflare.com
- Check network requests for blocked resources

## 📝 Test Results

**Date:** _____________
**Tester:** _____________
**Overall Status:** [ ] All Pass [ ] Minor Issues [ ] Major Issues

**Issues Found:**
- ________________________________
- ________________________________
- ________________________________

**Notes:**
- ________________________________
- ________________________________
