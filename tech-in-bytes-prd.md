# Tech-In-Bytes – Product Requirements Document (PRD)

## Note for Cursor IDE:

The Tech-In-Bytes Django project has already been created manually. The apps, project structure, admin site, and some HTML/CSS/JS basic files are already in place. Do not regenerate the scaffold from scratch. Instead, extend the existing codebase by implementing the features gradually step by step while asking me from 9.Milestones section point 6.Define URLs below in this file. Use the existing HTML/CSS files to base on and create the Django templates. Follow the app organization as already set up.

## 1\. Introduction

Tech-In-Bytes is a modern blogging platform for developers, IT professionals, and tech enthusiasts.
The goal of the MVP is to provide a minimal yet functional blogging application that allows users to create, read, update, and delete posts, interact with posts (likes, comments, tags), and manage their profiles — while remaining accessible to anonymous readers.

## 2\. Goals

  * Provide a clean, responsive blogging platform.
  * Enable content creation and interaction (CRUD, likes, comments, tags).
  * Allow anonymous browsing but require authentication for interactive actions.
  * Ensure scalability and maintainability with Django and modern best practices.
  * Prepare groundwork for future AI-powered features.

## 3\. Tech Stack

  * Frontend: HTML, CSS, Vanilla JavaScript
  * Backend: Django (Python)
  * Database: SQLite (dev) → PostgreSQL (prod)
  * Containerization: Docker
  * Deployment: AWS (EC2, S3, RDS, SES for future)
  * Email: Placeholder (console backend) for MVP

## 4\. Features (MVP Scope)

### Functional Requirements

  1. **Post Management (CRUD)**
      * Create, edit, delete, view posts.
      * Rich text editor optional (simple text fields in MVP).
  2. **Authentication**
      * Register, login, logout.
      * Password reset via email placeholder.
      * Password change
  3. **Pagination**
      * Posts paginated on listing pages.
  4. **Comments**
      * Logged-in users can comment on posts.
      * Display threaded comments with reply option.
  5. **Tagging & Tag Filter**
      * Posts can be tagged.
      * Filter posts by tag.
  6. **Related Posts Recommendation**
      * Display related posts by shared tags.
  7. **Recommendation Button (Email)**
      * Users can send post recommendations by email (console log in MVP).
  8. **Likes**
      * Like/unlike button for posts.
      * Liked posts page: User can view posts they liked.
  9. **Profile Management**
      * Edit profile information.
      * Delete account.
  10. **Search Engine**
      * Search posts by title/category/content/tags.
  11. **SEO-friendly URLs**
      * Posts: `/blog/<slug>/`
      * Tags: `/tags/<tag>/`
      * User profiles: `/accounts/<username>/`
  12. **Sitemap**
      * Auto-generated `sitemap.xml`
  13. **Admin Site**
      * Django admin enabled for managing users, posts, tags, comments.

## 5\. Page Structure & Navigation

  * Landing Page (/) → Highlights, recent posts, search bar.
  * All Posts Page (/blog/) → Paginated list with filters (by category, liked).
  * Single Post Page (/blog/<slug>/) → Post content, tags, related posts, comments, like/recommend.
  * Create Post Page (/blog/create/) → Form to create new post.
  * Manage Posts Page (/blog/manage/) → List of user’s posts (edit/delete).
  * About Page (/about/) → Info about the app.
  * Contact Page (/contact/) → Contact form (sends to console in MVP).
  * User Profile Page (/accounts/profile/) → Profile details, edit/delete account.

## 6\. User Roles & Permissions

  * **Anonymous User**
      * Can browse posts, search, filter by tags.
      * Cannot comment, like, create, or recommend posts.
  * **Authenticated User**
      * All of the above + create/edit/delete their posts.
      * Comment on posts.
      * Like posts.
      * Recommend posts via email (console).
      * Manage profile.
  * **Admin**
      * All permissions + manage all posts, users, and comments via Django Admin.

## 7\. Data Models (High-Level)

  * **User**
      * `username`
      * `email`
      * `password`
      * `profile` (OneToOne with additional fields like bio, avatar)
  * **Post**
      * `title` (string)
      * `slug` (unique, used in SEO-friendly URLs)
      * `content` (text)
      * `summary` (short text)
      * `author` (FK → User)
      * `tags` (M2M → Tag)
      * `image` (ImageField, upload path: `post_images/`, with validation for file size and minimum dimensions)
      * `status` (choices: Draft, Published)
      * `created_at` (auto timestamp)
      * `updated_at` (auto timestamp)
      * `published_at` (nullable timestamp, set when status changes to Published)
  * **Tag**
      * `name` (string)
      * `slug` (unique)
  * **Comment**
      * `post` (FK → Post)
      * `author` (FK → User)
      * `content` (text)
      * `parent` (self-relation for replies)
      * `created_at` (auto timestamp)
  * **Like**
      * `user` (FK → User)
      * `post` (FK → Post)
  * **Profile**
      * `user` (OneToOne → User)
      * `bio` (text, optional)
      * `avatar` (ImageField, optional, with validation similar to Post images)

## 8\. Django Project Structure (High-Level)

```
tech_bloggers/
│
├── manage.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env
│
├── tech_bloggers/          # Django project config
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│
├── apps/                   # All custom Django apps
│   ├── blog/               # Posts & comments
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── forms.py
│   │
│   ├── accounts/              # Authentication & profiles
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── forms.py
│   │
│   ├── core/               # Core utilities
│   │   ├── middleware.py
│   │   └── utils.py
│   │
│   └── pages/              # Static pages (about, contact, landing)
│       ├── views.py
│       └── urls.py
│       
│
├── templates/              # Global templates dir
│   ├── base.html
│   ├── includes/
│   │   ├── navbar.html
│   │   └── footer.html
│   │
│   ├── blog/
│   │   ├── all_posts.html
│   │   ├── single_post.html
│   │   ├── create_post.html
│   │   └── manage_posts.html
│   │
│   ├── accounts/
│   │   ├── login.html
│   │   ├── signup.html
│   │   └── profile.html
│   │   
│   │
│   └── pages/
│       ├── index.html
│       ├── about.html
│       └── contact.html
│
├── static/                 # Global static files
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/
│       └── (all app images)
│
└── media/                  # User uploaded media
    └── post_images/
```

## 9\. Milestones
  1. Initialize Django project.
  2. Create apps.
  3. Clarify app responsibilities.
  4. Define models and run migrations.
  5. Django Admin site setup.
  6. Define URLs.
  7. Implement templates and forms based on existing HTML/CSS/JS.
  8. Implement CRUD with CBV Views.
  9. Configure authentication (Django Auth).
  10. Add tags, likes, and comments.
  11. Configure search, SEO, and sitemap. 
  12. Post recommendation by email.
  13. Profile management.
  14. Deploy locally with Docker, then prepare AWS setup.

## 10\. Success Metrics
* User can create, edit, and publish posts.
* Users can like, comment, and search posts.
* Related posts appear by tag.
* SEO URLs & sitemap work.
* Admin can manage content.
* App is responsive and functional across devices.

## 11\. Risks & Mitigations
* Scalability: Start with SQLite, move to PostgreSQL for production.
* Email service: Placeholder until AWS SES or similar is integrated.
* AI features: Clearly out of MVP scope, but noted for future expansion.

## 12\. Future Enhancements
  * Follow Button → Users can follow other authors.
  * AI-powered features (AWS AI/ML):
      * Automatic post summarizer.
      * AI-generated images for posts.
      * Content moderation (detect offensive content).
      * Advanced post recommendations.
  * Social logins (Google/GitHub).

## 13\. Workflow Instructions for Cursor IDE
- Do not regenerate scaffolding or base templates.
- Implement features incrementally inside the existing apps.
- Reuse the provided HTML/CSS for templates; only add necessary Django template tags and context.
- Keep models, views, and forms inside their respective apps.
- Use class-based views when possible.
- For email recommendation, log emails to console as a placeholder.
- Add tests as you implement features.
