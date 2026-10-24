# 🍽️ FoodMart – Restaurant Online Management System

**FoodMart** is an online food ordering and restaurant management platform developed as an academic semester mini-project. The system delivers two dedicated modules: a **Customer Ordering & Table Reservation Portal** and a **Restaurant Admin Management Dashboard**.

---

## 🌟 Key Features

### 1. 👤 Customer / User Module
- **Account Management**: Customer registration, login, logout, and profile management with saved delivery addresses.
- **Menu Catalog**:
  - Filter by Categories (*Starters & Appetizers, Main Course, Pizzas & Burgers, Desserts & Sweets, Beverages*).
  - Search dishes by name or keywords.
  - Dietary toggles (*100% Pure Veg* vs *Non-Veg*).
  - Price sorting (Low to High, High to Low).
  - Nutritional facts & estimated preparation time badges.
- **Interactive Cart & Checkout**:
  - Add to cart with quantity stepper (`+` / `-`), remove items, and live order total.
  - Delivery address form with instructions/landmarks.
  - Simulated payment options: **Cash on Delivery (COD)**, **Card**, and **UPI**.
- **Live Order Tracking**:
  - Visual 5-stage pipeline: `Order Placed` ➔ `Confirmed` ➔ `In Kitchen (Preparing)` ➔ `Out for Delivery` ➔ `Delivered`.
  - Delivery partner information (Rider Name, Contact, Estimated Arrival Time).
  - Printable invoice receipt with itemized breakdown.
- **Dine-In Table Reservation**:
  - Reserve dining tables by selecting date, time slot, and guest count.
  - Choose seating ambiance (*Main Dining Hall, Window View, Romantic Booth, Outdoor Garden Terrace, Family Lounge*).
  - View booking history and cancel upcoming reservations with one click.

---

### 2. 🛡️ Restaurant Admin Module
- **Executive Dashboard**:
  - KPI metric cards: *Total Delivered Revenue, Total Orders, Active Kitchen Orders, Today's Reservations, Menu Items, Registered Diners*.
  - Visual Doughnut Chart powered by Chart.js showing order status distribution.
  - Recent Orders & Upcoming Table Reservations quick-action tables.
- **Food Menu CRUD**:
  - Add new dishes with name, category, price, prep time, calories, veg/non-veg flag, and image URLs.
  - Edit existing dishes and prices.
  - Delete or toggle availability (In Stock / Sold Out).
- **Category Management**:
  - Create and delete categories with icons and descriptions.
- **Customer Orders & Delivery Dispatch**:
  - Filter orders by status (*Pending, Confirmed, Preparing, Out for Delivery, Delivered, Cancelled*).
  - Update order workflow and payment statuses.
  - Dispatch deliveries: Assign rider name, phone number, and estimated arrival time.
- **Table Reservation Management**:
  - Filter bookings by date and status.
  - 1-click **Confirm** or **Cancel** reservation requests.
- **Customer Directory**:
  - View registered customers with contact info, total orders placed, and table booking counts.
- **Reports & Analytics**:
  - Net sales revenue report.
  - Top 5 best-selling dishes by portions and revenue.
  - Revenue by category and payment method breakdowns.
  - Print / export reports.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Django 6.0+

### 2. Database Setup (Already Migrated & Seeded)
If you ever want to re-run migrations or re-seed starter data:
```bash
python manage.py migrate
python manage.py seed_data
```

### 3. Run the Development Server
```bash
python manage.py runserver
```
Open your browser and navigate to:
```
http://127.0.0.1:8000/
```

---

## 🔑 Demo Login Credentials

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Restaurant Admin** | `admin` | `admin123` | Full access to Admin Portal (`/portal/`) & Django Admin (`/django-admin/`) |
| **Demo Customer** | `customer` | `customer123` | Ordering food, tracking orders, and reserving tables |

*You can also register any new customer account directly from the website.*

---

## 📂 Project Structure

```
d:/MINI PROJECT SEM1/
├── foodmart/                      # Django project configuration
│   ├── settings.py                # Installed apps, templates, static/media
│   ├── urls.py                    # Root URL router
│   └── wsgi.py
├── restaurant/                    # Main application
│   ├── models.py                  # Category, FoodItem, RestaurantTable, TableReservation, Order, OrderItem, CustomerProfile
│   ├── views.py                   # Customer ordering + Admin management views
│   ├── forms.py                   # Registration, Checkout, Reservation, FoodItem forms
│   ├── urls.py                    # App URLs
│   ├── context_processors.py      # Cart badge count & subtotal calculation
│   ├── admin.py                   # Standard Django Admin registration
│   ├── tests.py                   # Automated test suite
│   └── management/commands/
│       └── seed_data.py           # Starter data populator
├── templates/restaurant/          # Modern Tailwind CSS HTML templates
│   ├── base.html                  # Global layout with responsive navbar & footer
│   ├── home.html                  # Hero, featured dishes, categories, testimonials
│   ├── menu.html                  # Searchable menu with filters & sorting
│   ├── food_detail.html           # Detailed dish view with quantity selector
│   ├── cart.html                  # Shopping cart with quantity stepper
│   ├── checkout.html              # Delivery address and payment selection
│   ├── order_detail.html          # Live 5-stage tracking pipeline & printable invoice
│   ├── order_history.html         # Customer order history
│   ├── table_reservation.html     # Table booking with dining zones
│   ├── reservation_history.html   # Customer reservation history
│   ├── auth/                      # Login & Register views
│   └── admin_portal/              # Comprehensive Restaurant Admin Dashboard
│       ├── base_admin.html        # Admin layout with sidebar
│       ├── dashboard.html         # KPI cards, Chart.js chart, recent tables/orders
│       ├── food_list.html         # Menu items management
│       ├── food_form.html         # Add / Edit food dish
│       ├── category_list.html     # Categories management
│       ├── order_list.html        # Orders pipeline with filters
│       ├── order_detail.html      # Dispatch rider & update status
│       ├── reservation_list.html  # Manage table bookings
│       ├── customer_list.html     # Customer directory
│       └── reports.html           # Sales analytics & top dishes
├── static/                        # Custom CSS & assets
├── manage.py
└── requirements.txt
```

---

## 🧪 Running Automated Tests
To run the automated test suite:
```bash
python manage.py test
```
All 6 test cases for public views, cart workflows, checkouts, live tracking, table reservations, and admin access run automatically.
