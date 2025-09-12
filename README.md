# Tech Bloggers

A modern blogging platform for developers, IT professionals, and tech enthusiasts.

## Features

- User authentication with email verification
- Create, read, update, and delete blog posts
- Tag system for posts
- Comment system
- Like/Unlike posts
- User profiles with avatars
- Search functionality
- SEO-friendly URLs
- Responsive design

## Tech Stack

- Backend: Django 5.2
- Frontend: HTML, CSS, Vanilla JavaScript
- Database: SQLite (dev) / PostgreSQL (prod)
- Image Processing: Pillow
- Tag System: django-taggit

## Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd tech-bloggers
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a .env file in the project root and add your environment variables:

```
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

5. Run migrations:

```bash
python manage.py migrate
```

6. Create a superuser:

```bash
python manage.py createsuperuser
```

7. Run the development server:

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to see the application.

## Development

- The project uses Python's `python-dotenv` for environment variables
- Media files are stored in the `media/` directory
- Static files are collected to `static/`
- Templates are in the `templates/` directory

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
