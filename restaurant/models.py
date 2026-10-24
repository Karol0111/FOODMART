import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default="fa-utensils", help_text="FontAwesome icon name, e.g. fa-burger")
    image_url = models.URLField(blank=True, max_length=500)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class FoodItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='food_items')
    name = models.CharField(max_length=150)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image_url = models.URLField(max_length=500, blank=True)
    is_veg = models.BooleanField(default=True, help_text="Checked for Vegetarian, unchecked for Non-Veg")
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    preparation_time = models.CharField(max_length=50, default="20-25 mins")
    calories = models.CharField(max_length=50, blank=True, default="350 kcal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', 'name']

    def __str__(self):
        return f"{self.name} - ₹{self.price}"


class RestaurantTable(models.Model):
    LOCATION_CHOICES = [
        ('Main Dining Hall', 'Main Dining Hall'),
        ('Window View', 'Window View'),
        ('Romantic Booth', 'Romantic Booth'),
        ('Outdoor Garden Terrace', 'Outdoor Garden Terrace'),
        ('Family Lounge', 'Family Lounge'),
    ]
    table_number = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField(default=4)
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES, default='Main Dining Hall')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['table_number']

    def __str__(self):
        return f"Table {self.table_number} ({self.capacity} Guests - {self.location})"


class TableReservation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Confirmation'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    reservation_code = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    table = models.ForeignKey(RestaurantTable, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    guest_count = models.PositiveIntegerField(default=2)
    special_requests = models.TextField(blank=True, help_text="e.g., Birthday celebration, high chair, quiet corner")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reservation_date', '-reservation_time']

    def save(self, *args, **kwargs):
        if not self.reservation_code:
            self.reservation_code = f"RES-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reservation_code} - {self.customer_name} ({self.reservation_date} {self.reservation_time})"


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Order Placed'),
        ('CONFIRMED', 'Order Confirmed'),
        ('PREPARING', 'In Kitchen / Preparing'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('CARD', 'Credit / Debit Card'),
        ('UPI', 'UPI / Online Payment'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
    ]

    order_number = models.CharField(max_length=30, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    delivery_address = models.TextField()
    delivery_city = models.CharField(max_length=100, default="City Center")
    delivery_notes = models.TextField(blank=True, help_text="Landmarks, gate codes, etc.")
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=30.00)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='COD')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    order_status = models.CharField(max_length=25, choices=ORDER_STATUS_CHOICES, default='PENDING')
    
    delivery_person_name = models.CharField(max_length=100, blank=True, default="FoodMart Express Rider")
    delivery_person_phone = models.CharField(max_length=20, blank=True, default="+91 98765 43210")
    estimated_delivery_time = models.CharField(max_length=50, blank=True, default="30 - 45 mins")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            import datetime
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            self.order_number = f"FM-{date_str}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.customer_name} (₹{self.total_amount})"

    @property
    def grand_total(self):
        return self.total_amount + self.delivery_fee

    @property
    def status_step(self):
        mapping = {
            'PENDING': 1,
            'CONFIRMED': 2,
            'PREPARING': 3,
            'OUT_FOR_DELIVERY': 4,
            'DELIVERED': 5,
            'CANCELLED': 0,
        }
        return mapping.get(self.order_status, 1)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.SET_NULL, null=True, blank=True)
    food_name = models.CharField(max_length=150)
    food_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.food_name} in {self.order.order_number}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True, default="City Center")

    def __str__(self):
        return f"Profile of {self.user.username}"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = Order.PAYMENT_METHOD_CHOICES
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success / Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=50, unique=True, editable=False)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='COD')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    payment_gateway = models.CharField(max_length=50, default='FoodMart Direct')
    gateway_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import datetime
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            self.transaction_id = f"PAY-{date_str}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_id} - Order #{self.order.order_number} (₹{self.amount}) [{self.status}]"

