# Django E-commerce Management System

A modern e-commerce management system built with Django, featuring inventory management, purchase orders, invoices, and comprehensive dashboard analytics.


## Setup Instructions

### Prerequisites

- Python 3.10+ installed
- Git installed
- Basic knowledge of command line operations
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/Django-E-commerce.git
cd Django-E-commerce
```

### Step 2: Set Up a Virtual Environment

#### On Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### On macOS/Linux
```bash
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

The application uses a `.env` file for configuration. You'll find an example file named `.env.example` in the repository.

1. Copy the example file:
```bash
# On Windows
copy .env.example .env

# On macOS/Linux
cp .env.example .env
```

2. Edit the `.env` file to configure your database:
   - To use PostgreSQL, set the `DATABASE_URL` variable:
     ```
     DATABASE_URL=postgresql://username:password@host:port/database_name?sslmode=require
     ```
   - To use the default SQLite database, you can leave the file empty or comment out the DATABASE_URL line

#### Example .env File
```
# PostgreSQL Database Configuration
DATABASE_URL=postgresql://neondb_owner:npg_kSAYgG4TN2oL@ep-rapid-wave-a4rxjbl8-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require

# Comment out the above line if you want to use SQLite instead
```

### Step 5: Fix Template Configuration

Before running migrations, you need to ensure the template configuration is correct in `ecommerce/settings.py`.

Make sure the TEMPLATES setting has `APP_DIRS` set to `False` when `loaders` is defined:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': False,  # Must be False when loaders is defined
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]
```

### Step 6: Set Up the Database

```bash
# Apply migrations to create database tables
python manage.py migrate
```

### Step 7: Create a Superuser (Admin Account)

Creating a superuser is essential as it gives you access to the Django admin interface where you'll manage products, invoices, and other e-commerce data.

```bash
python manage.py createsuperuser
```

You'll be prompted to enter:
- **Username**: Choose a username (e.g., admin)
- **Email Address**: Enter your email
- **Password**: Create a secure password (it won't be visible when typing)
- **Password Confirmation**: Re-enter your password

Example:
```
Username: admin
Email address: admin@example.com
Password: 
Password (again): 
Superuser created successfully.
```

#### Using the Superuser Account

After creating the superuser, you can:
1. Access the admin interface at http://127.0.0.1:8000/admin/
2. Log in with your superuser credentials
3. Start managing your e-commerce platform:
   - Add products to your inventory
   - Create purchase orders
   - Generate invoices
   - View dashboard analytics
   - Set up user permissions and groups


### Step 8: Collect Static Files

```bash
python manage.py collectstatic
```

### Step 9: Run the Development Server

```bash
python manage.py runserver
```

### Step 10: Access the Application

- **Main website**: http://127.0.0.1:8000/
- **Admin interface**: http://127.0.0.1:8000/admin/
- **Dashboard**: http://127.0.0.1:8000/dashboard/

## Usage Guide

### Admin Interface

The admin interface is where you'll manage most of the e-commerce operations:

1. **Products**: Add, edit, and delete products, monitor stock levels
2. **Purchase Orders**: Create purchase orders from vendors, track order status
3. **Invoices**: Create customer invoices, mark as paid, export to Excel
4. **Users & Groups**: Manage user access and permissions

### Creating Invoices

1. Go to Admin > Store > Invoices
2. Click "Add Invoice"
3. Fill in customer details, set due date and status
4. Add line items (products, quantity, price)
5. Save the invoice

### Exporting Invoices to Excel

1. Go to Admin > Store > Invoices
2. Select one or more invoices
3. From the "Action" dropdown, select "Export to XLSX"
4. Click "Go" to download the Excel file

## Troubleshooting

### Template Configuration Error

If you see an error like:
```
django.core.exceptions.ImproperlyConfigured: app_dirs must not be set when loaders is defined.
```

Edit `ecommerce/settings.py` and set `APP_DIRS` to `False` in the TEMPLATES configuration.

### Database Connection Issues

- If using PostgreSQL and you have connection problems, check your `.env` file for the correct database URL
- To fall back to SQLite, remove or comment out the DATABASE_URL from the `.env` file

### Static Files Not Loading

Run `python manage.py collectstatic` to collect all static files to the STATIC_ROOT directory.

## Project Structure

- `ecommerce/`: Project settings and URL configuration
- `store/`: Main application with models, views, and admin configurations
  - `models.py`: Data models (Product, PurchaseOrder, Invoice)
  - `admin.py`: Admin interface customizations
  - `views.py`: View controllers for the frontend
  - `queries.py`: Complex database queries and calculations
- `static/`: Static files (CSS, JavaScript)
  - `admin/css/`: Custom admin styling
- `templates/`: HTML templates
  - `admin/`: Custom admin templates
  - `store/`: Frontend templates


