# 🍽️ FoodMart – Restaurant Online Management System

**FoodMart** is a full-featured restaurant management and online food ordering platform developed as an academic semester mini-project. Built using **Python**, **Django**, and modern front-end styling with **Tailwind CSS**, the system provides a dual-interface architecture:
1. **Customer Ordering & Table Reservation Storefront**
2. **Dedicated Restaurant Admin & Operations Portal** (along with standard **Django Backend Admin**)

---

## 🔑 Demo & Admin Credentials

Use the pre-configured credentials below to explore the application immediately:

| Role | Username | Password | Purpose & Privileges | Direct URL |
| :--- | :--- | :--- | :--- | :--- |
| **Restaurant Admin** | `admin` | `admin123` | Full access to Management Portal (`/portal/`) and Django Admin (`/django-admin/`) | [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/) |
| **Demo Customer** | `customer` | `customer123` | Food ordering, cart checkout, order tracking, and table reservations | [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/) |

> **Tip**: When logging in as `admin` via the main login page (`/login/`), you will automatically be redirected directly to the **Restaurant Admin Portal** (`/portal/`).

---

## 🚀 How to Run the Project & Server

Follow these step-by-step instructions to set up and run FoodMart locally.

### 1. Prerequisites
- **Python**: Version `3.10` or higher (tested with Python `3.14`)
- **pip**: Python package manager
- **Git** (optional, for cloning)

---

### 2. Open Project Directory
Open your terminal (PowerShell, Command Prompt, or bash) and navigate to the project directory:
```bash
cd "d:\MINI PROJECT SEM1"
```

---

### 3. Create & Activate a Virtual Environment (Recommended)

- **On Windows (PowerShell)**:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\activate
  ```

- **On Windows (Command Prompt)**:
  ```cmd
  python -m venv .venv
  .\.venv\Scripts\activate.bat
  ```

- **On Linux / macOS**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

---

### 4. Install Dependencies
Install all required Python packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

### 5. Apply Database Migrations
Run the Django migration commands to create all database tables in `db.sqlite3`:
```bash
python manage.py migrate
```

---

### 6. Seed Demo Data & Admin Account (Recommended)
FoodMart comes with a built-in seeding utility that automatically populates categories, dishes, dine-in tables, demo orders, delivery partners, and the default `admin` and `customer` accounts:
```bash
python manage.py seed_data
```

> **Note on Fresh Reset**: If you ever want to wipe existing demo orders, payments, and reservations and regenerate fresh sample data:
> ```bash
> python manage.py seed_data --reset
> ```

---

### 7. (Optional) Create a Custom Superuser
If you wish to create your own custom administrator account with your own credentials:
```bash
python manage.py createsuperuser
```
Follow the terminal prompts for username, email, and password.

---

### 8. Start the Django Development Server
Launch the local web server:
```bash
python manage.py runserver
```

By default, the server runs on port `8000`. You will see output similar to:
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
Django version 6.0, using settings 'foodmart.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

#### Running on an Alternative Port:
If port `8000` is already in use by another program on your system, specify a different port (e.g., `8080`):
```bash
python manage.py runserver 8080
```
Then access the site at `http://127.0.0.1:8080/`.

---

### 9. Access the Web Application
Open your browser and navigate to:
- **Main Website / Customer Storefront**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Restaurant Management Portal**: [http://127.0.0.1:8000/portal/](http://127.0.0.1:8000/portal/)
- **Standard Django Admin**: [http://127.0.0.1:8000/django-admin/](http://127.0.0.1:8000/django-admin/)

---

## 🛡️ Admin Module Overview & Features

FoodMart includes two distinct administrative interfaces tailored to different operational needs:

```
┌─────────────────────────────────────────────────────────────┐
│                       ADMIN SURFACES                        │
├──────────────────────────────┬──────────────────────────────┤
│ 1. Restaurant Operations     │ 2. Backend Django Admin      │
│    Portal (/portal/)         │    (/django-admin/)          │
│ • Custom Tailwind Dashboard  │ • Built-in Django ORM Admin  │
│ • Order Pipeline & Dispatch  │ • Raw Table Records          │
│ • Dish CRUD & Stock Toggles  │ • User Group Permissions     │
│ • Table Reservation Control  │ • Database Inspection        │
│ • Sales Analytics & Charts   │                              │
└──────────────────────────────┴──────────────────────────────┘
```

### 1. 📊 Custom Restaurant Operations Portal (`/portal/`)

Accessible to staff and superusers at [http://127.0.0.1:8000/portal/](http://127.0.0.1:8000/portal/). Designed for daily restaurant managers, kitchen chefs, and delivery coordinators:

1. **Executive Dashboard (`/portal/`)**:
   - **Real-Time KPI Cards**: Delivers at-a-glance metrics for *Total Delivered Revenue*, *All Active Orders*, *Today's Table Bookings*, *Pending Reservations*, *Active Menu Items*, and *Registered Diners*.
   - **Interactive Order Status Chart**: A dynamic doughnut chart (powered by Chart.js) depicting order status distribution (*Pending, Preparing, Out for Delivery, Delivered, Cancelled*).
   - **Quick Action Lists**: Recent incoming orders and upcoming dining reservations.

2. **Food Menu Catalog CRUD (`/portal/foods/`)**:
   - **View All Dishes**: Search dishes by keyword, filter by category (*Starters, Main Course, Pizzas, Desserts, Beverages*), or toggle by dietary type (*Veg* vs *Non-Veg*).
   - **Add New Food Item (`/portal/foods/add/`)**: Create items with name, category, price, preparation time, calories, dietary tag, description, and image URL.
   - **Edit Dish (`/portal/foods/<pk>/edit/`)**: Update prices, availability (*In Stock* / *Sold Out*), or featured flags.
   - **Delete Dish (`/portal/foods/<pk>/delete/`)**: Instant AJAX deletion with toast feedback.

3. **Category Management (`/portal/categories/`)**:
   - Create new menu categories with custom FontAwesome icons (e.g., `fa-pizza-slice`, `fa-burger`, `fa-mug-hot`).
   - Track dish count per category and delete categories.

4. **Order Management & Delivery Dispatch (`/portal/orders/`)**:
   - **Status Filtering**: Filter orders across 6 states: *All, Pending, Confirmed, Preparing, Out for Delivery, Delivered, Cancelled*.
   - **Order Detail & Workflow (`/portal/orders/<pk>/`)**:
     - View ordered line items, quantities, prices, delivery address, and notes.
     - Advance order workflow through the lifecycle: `Pending` ➔ `Confirmed` ➔ `In Kitchen` ➔ `Out for Delivery` ➔ `Delivered`.
     - Update payment status (*Pending, Completed, Failed*).
     - **Delivery Rider Dispatch**: Assign a delivery partner, record contact number, and set estimated arrival time (ETA).
     - **Print Kitchen Slip**: Direct kitchen ticket printing (`/order/<order_number>/kitchen-slip/`).
     - **Print Invoice**: Professional customer billing invoice (`/order/<order_number>/invoice/`).

5. **Table Reservation Management (`/portal/reservations/`)**:
   - List and filter dining reservations by date and status (*Pending, Confirmed, Completed, Cancelled*).
   - 1-Click **Confirm** or **Cancel** action buttons.
   - **Atomic Conflict Safeguard**: Prevents overlapping double-bookings on the same physical table for identical dates and time slots.

6. **Customer Directory (`/portal/customers/`)**:
   - Complete directory of registered diners showing contact phone, email, registration date, total orders placed, and table booking counts.

7. **Reports & Sales Analytics (`/portal/reports/`)**:
   - Summary of gross and completed net sales.
   - **Top 5 Best-Selling Dishes**: Ranked by portion count and revenue generated.
   - **Category Sales Breakdown**: Revenue distribution across food categories.
   - **Payment Method Split**: Proportion of orders placed via Cash on Delivery (COD), Card, and UPI.
   - Dedicated Print/Export feature for administrative reporting.

---

### 2. ⚙️ Standard Django Backend Admin (`/django-admin/`)

Accessible to superusers at [http://127.0.0.1:8000/django-admin/](http://127.0.0.1:8000/django-admin/):
- **Models Registered**:
  - `Categories` (with auto-generated slugs)
  - `FoodItems` (with inline editable pricing and availability flags)
  - `RestaurantTables` (capacity and seating zones)
  - `TableReservations` (date, time, status, guest count)
  - `Orders` (with tabular inlines for `OrderItem` and `Payment`)
  - `Payments` (transaction ID, gateway reference, timestamp)
  - `DeliveryPartners` (rider name, phone, active status)
  - `CustomerProfiles` (phone number, address, city)
  - `Users & Groups` (Django Auth permission management)

---

## 🌟 Customer Module Features

For customers and diners visiting the site:
- **Menu Catalog**: Filter by category, veg/non-veg toggle, keyword search, price sorting, calories and prep-time badges.
- **Cart & Checkout**: Interactive quantity stepper (`+` / `-`), delivery instructions, and payment methods (COD, Card, UPI).
- **Live Order Tracking**: Visual 5-stage progress pipeline (`Placed` ➔ `Confirmed` ➔ `Kitchen` ➔ `Rider Picked` ➔ `Delivered`) with assigned rider details and printable receipts.
- **Table Reservation**: Book tables by party size, date, time slot, and ambiance (*Main Hall, Window View, Romantic Booth, Garden Terrace, Family Lounge*).
- **Customer Account**: Profile address management, order history, and reservation cancellations.

---

## 🗺️ Complete URL Route Map

| URL Path | View Name | Description | Access Level |
| :--- | :--- | :--- | :--- |
| `/` | `home` | Landing page, hero, featured dishes, and testimonials | Public |
| `/menu/` | `menu` | Full searchable and filterable menu catalog | Public |
| `/food/<id>/` | `food_detail` | Detailed dish information & add to cart | Public |
| `/cart/` | `cart` | Shopping cart view with quantity stepper | Public |
| `/checkout/` | `checkout` | Address form & simulated payment options | Logged-in Customer |
| `/order/<order_number>/` | `order_detail` | Live 5-stage visual order tracker & delivery info | Customer / Staff |
| `/order/<order_number>/invoice/` | `order_invoice` | Printable customer bill invoice | Customer / Staff |
| `/order/<order_number>/kitchen-slip/` | `order_kitchen_slip` | Printable chef kitchen slip | Customer / Staff |
| `/my-orders/` | `order_history` | Customer order history log | Logged-in Customer |
| `/table-reservation/` | `table_reservation` | Dine-in table booking form | Public / Customer |
| `/my-reservations/` | `reservation_history` | Customer reservation history & cancellation | Logged-in Customer |
| `/register/` | `register` | Customer registration | Public |
| `/login/` | `login` | Login (redirects staff to `/portal/`, customers to `/`) | Public |
| `/logout/` | `logout` | Logout session | Logged-in User |
| `/profile/` | `profile` | Customer profile & default address | Logged-in Customer |
| **`/portal/`** | **`admin_dashboard`** | **Executive KPI Dashboard & Chart.js order analytics** | **Admin / Staff** |
| `/portal/foods/` | `admin_food_list` | Dish management & stock toggles | Admin / Staff |
| `/portal/foods/add/` | `admin_food_add` | Add new menu item | Admin / Staff |
| `/portal/foods/<id>/edit/` | `admin_food_edit` | Edit menu dish & price | Admin / Staff |
| `/portal/categories/` | `admin_category_list` | Create & delete categories | Admin / Staff |
| `/portal/orders/` | `admin_order_list` | Filter & manage incoming customer orders | Admin / Staff |
| `/portal/orders/<id>/` | `admin_order_detail` | Order status workflow & rider dispatch | Admin / Staff |
| `/portal/reservations/` | `admin_reservation_list`| View, confirm, and cancel table bookings | Admin / Staff |
| `/portal/customers/` | `admin_customer_list` | Customer directory & dining history | Admin / Staff |
| `/portal/reports/` | `admin_reports` | Sales reports, top dishes & payment splits | Admin / Staff |
| **`/django-admin/`** | `admin:index` | **Standard Django administration interface** | **Superuser** |

---

## 📂 Project Structure

```
d:/MINI PROJECT SEM1/
├── foodmart/                      # Django project configuration
│   ├── settings.py                # Database, static/media, installed apps
│   ├── urls.py                    # Root URL router
│   ├── wsgi.py                    # WSGI entry point
│   └── asgi.py                    # ASGI entry point
├── restaurant/                    # Core restaurant application
│   ├── models.py                  # Category, FoodItem, RestaurantTable, TableReservation, Order, OrderItem, Payment, DeliveryPartner, CustomerProfile
│   ├── views.py                   # Customer ordering + Admin management views
│   ├── forms.py                   # Registration, Checkout, Reservation, FoodItem, Category forms
│   ├── urls.py                    # App URLs
│   ├── context_processors.py      # Cart badge count & subtotal calculation
│   ├── admin.py                   # Django admin model registrations & inlines
│   ├── tests.py                   # Automated test suite
│   └── management/commands/
│       └── seed_data.py           # Starter data populator (--reset supported)
├── templates/restaurant/          # Modern Tailwind CSS HTML templates
│   ├── base.html                  # Global layout with responsive navbar & footer
│   ├── home.html                  # Landing page hero, categories, featured items
│   ├── menu.html                  # Searchable menu with filters & sorting
│   ├── food_detail.html           # Detailed dish view with quantity selector
│   ├── cart.html                  # Shopping cart with quantity stepper
│   ├── checkout.html              # Delivery address and payment selection
│   ├── order_detail.html          # Live 5-stage tracking pipeline & printable invoice
│   ├── order_history.html         # Customer order history
│   ├── table_reservation.html     # Table booking with dining zones
│   ├── reservation_history.html   # Customer reservation history
│   ├── auth/                      # Login & Register views
│   │   ├── login.html
│   │   └── register.html
│   └── admin_portal/              # Comprehensive Restaurant Admin Dashboard
│       ├── base_admin.html        # Admin layout with sidebar navigation
│       ├── dashboard.html         # KPI cards, Chart.js chart, recent tables/orders
│       ├── food_list.html         # Menu items management & stock toggles
│       ├── food_form.html         # Add / Edit food dish form
│       ├── category_list.html     # Categories management
│       ├── order_list.html        # Orders pipeline with status tabs
│       ├── order_detail.html      # Dispatch rider & update status
│       ├── reservation_list.html  # Manage table bookings
│       ├── customer_list.html     # Customer directory
│       └── reports.html           # Sales analytics & top dishes
├── static/                        # Custom CSS, fonts, and assets
├── db.sqlite3                     # SQLite database file
├── manage.py                      # Django management script
├── requirements.txt               # Project dependencies (Django>=6.0.0)
└── README.md                      # Project documentation
```

---

## 🧪 Running Automated Tests

Run the comprehensive automated test suite to verify all core workflows:
```bash
python manage.py test
```

The test suite covers:
- Public view response codes (Home, Menu, Dish details)
- Cart manipulation and session calculation
- Checkout and order creation
- Live order tracking pipeline
- Dine-in table reservations and conflict handling
- Admin portal access control (`is_admin` permission checks)
- Django admin access
