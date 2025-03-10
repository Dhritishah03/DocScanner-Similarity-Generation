# Document Scanner and Credit Management System

This project is a document scanning and credit management system built with Django. It allows users to scan documents, request credits, and view analytics.

## Features

- User registration and authentication
- Document scanning with text extraction
- Credit management and requests
- Admin dashboard for managing credit requests and viewing analytics

## Prerequisites

- Python 3.8+
- Django 3.2+

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Dhritishah03/DocScanner-Similarity-Generation.git
cd DocScanner-Similarity-Generation
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
cd scanner
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Database (Default: SQLite3)

By default, the project uses SQLite, so no additional configuration is needed. If using a different database, update the `DATABASES` setting in `scanner/settings.py`.

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 5. Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a Superuser

```bash
python manage.py createsuperuser
```

### 7. Link a Profile to the Superuser

If you need to link a profile to the superuser, use the Django shell:

```bash
python manage.py shell
```

Then, run the following commands inside the shell:

```python
from django.contrib.auth import get_user_model
from your_app.models import Profile  # Replace `your_app` with the actual app name

User = get_user_model()
superuser = User.objects.get(username='your_superuser_username')
profile = Profile.objects.create(user=superuser, additional_field='value')  # Add required fields
print(f"Profile linked to superuser: {profile}")
```

### 8. Run the Development Server

```bash
python manage.py runserver
```

### 9. Access the Application

Open your web browser and go to `http://127.0.0.1:8000/` to access the application.

## Usage

- Register a new user or log in with an existing account.
- Scan documents and view the extracted text.
- Request additional credits if your current credits are exhausted.
- Admins can manage credit requests and view analytics.

