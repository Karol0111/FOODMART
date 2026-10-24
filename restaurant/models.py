"""
FoodMart models, normalized to 3NF.

What changed compared with the original (see NORMALIZATION notes inline):

1. DeliveryPartner table added. Rider name/phone no longer live on Order
   (phone depended on name, not on the order -> transitive dependency).
2. Order.total_amount and OrderItem.subtotal are no longer stored columns.
   They are derived from quantity * food_price, so they are computed.
3. Order.payment_method / Order.payment_status removed. Payment is the single
   source of truth; Order exposes read-only properties that look it up.
4. FoodItem.preparation_time ("15-20 mins") and calories ("320 kcal") were
   composite strings (not atomic). Now stored as integers; properties keep the
   old display strings for templates.
5. Integrity constraints added: no double-booking of a table slot, quantity >= 1,
   guest_count >= 1 and guest_count <= table capacity.

Deliberate snapshot columns that are KEPT (and why):
- OrderItem.food_name / food_price: price actually paid, so editing a dish later
  does not rewrite old invoices.
- Order.customer_* / delivery_address / delivery_city and
  TableReservation.customer_*: contact details for THAT order/booking (guests
  have no User row; a logged-in user may order for someone else).
- Payment.amount: amount actually charged (supports partial payments/refunds).
"""
import uuid
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.text import slugify


# Shared by Payment (stored) and Order (kept as a class attribute so checkout forms
# that read Order.PAYMENT_METHOD_CHOICES keep working).
PAYMENT_METHOD_CHOICES = [
    ('COD', 'Cash on Delivery'),
    ('CARD', 'Credit / Debit Card'),
    ('UPI', 'UPI / Online Payment'),
]


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

    # NORMALIZATION: atomic, typed values instead of "15-20 mins" / "320 kcal".
    prep_time_min = models.PositiveSmallIntegerField(default=20, help_text="Minimum preparation time (minutes)")
    prep_time_max = models.PositiveSmallIntegerField(default=25, help_text="Maximum preparation time (minutes)")
    calories_kcal = models.PositiveIntegerField(null=True, blank=True, help_text="Calories in kcal")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', 'name']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(prep_time_max__gte=F('prep_time_min')),
                name='fooditem_prep_max_gte_min',
            ),
        ]

    # Display helpers: templates that used {{ item.preparation_time }} and
    # {{ item.calories }} keep working because these properties return the old strings.
    @property
    def preparation_time(self):
        if self.prep_time_min == self.prep_time_max:
            return f"{self.prep_time_min} mins"
        return f"{self.prep_time_min}-{self.prep_time_max} mins"

    @property
    def calories(self):
        return f"{self.calories_kcal} kcal" if self.calories_kcal is not None else ""

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
    # Booking contact snapshot (guests have no User; a user may book for someone else).
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    table = models.ForeignKey(RestaurantTable, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    guest_count = models.PositiveIntegerField(default=2, validators=[MinValueValidator(1)])
    special_requests = models.TextField(blank=True, help_text="e.g., Birthday celebration, high chair, quiet corner")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reservation_date', '-reservation_time']
        constraints = [
            # One active booking per table per date/time slot.
            models.UniqueConstraint(
                fields=['table', 'reservation_date', 'reservation_time'],
                condition=~models.Q(status='CANCELLED'),
                name='unique_active_table_slot',
            ),
            models.CheckConstraint(condition=models.Q(guest_count__gte=1), name='reservation_guest_count_gte_1'),
        ]

    def clean(self):
        # Runs in ModelForms / full_clean(); the DB constraints above are the safety net.
        if self.table_id and self.guest_count and self.guest_count > self.table.capacity:
            raise ValidationError(
                f"Table {self.table.table_number} seats only {self.table.capacity} guests."
            )

    def save(self, *args, **kwargs):
        if not self.reservation_code:
            self.reservation_code = f"RES-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reservation_code} - {self.customer_name} ({self.reservation_date} {self.reservation_time})"


class DeliveryPartner(models.Model):
    """NORMALIZATION: rider phone depends on the rider, not on the order."""
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.phone})"


class OrderQuerySet(models.QuerySet):
    """Database-side totals for reports/dashboards (Sum over a derived value)."""

    def with_totals(self):
        money = DecimalField(max_digits=12, decimal_places=2)
        line_total = ExpressionWrapper(F('items__quantity') * F('items__food_price'), output_field=money)
        return self.annotate(
            items_total_db=Coalesce(Sum(line_total), Value(Decimal('0.00')), output_field=money),
        ).annotate(
            grand_total_db=ExpressionWrapper(F('items_total_db') + F('delivery_fee'), output_field=money),
        )


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Order Placed'),
        ('CONFIRMED', 'Order Confirmed'),
        ('PREPARING', 'In Kitchen / Preparing'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    PAYMENT_METHOD_CHOICES = PAYMENT_METHOD_CHOICES

    order_number = models.CharField(max_length=30, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    # Delivery contact snapshot for THIS order (guest checkout / ordering for someone else).
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    delivery_address = models.TextField()
    delivery_city = models.CharField(max_length=100, default="City Center")
    delivery_notes = models.TextField(blank=True, help_text="Landmarks, gate codes, etc.")

    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('30.00'))
    order_status = models.CharField(max_length=25, choices=ORDER_STATUS_CHOICES, default='PENDING')

    # NORMALIZATION: rider details live in DeliveryPartner (null until dispatched).
    delivery_partner = models.ForeignKey(
        DeliveryPartner, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
    )
    estimated_delivery_time = models.CharField(max_length=50, blank=True, default="30 - 45 mins")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            date_str = timezone.localdate().strftime("%Y%m%d")
            self.order_number = f"FM-{date_str}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.customer_name} (₹{self.grand_total})"

    # ---- Derived values (no longer stored) --------------------------------
    @property
    def total_amount(self):
        """Items total BEFORE the delivery fee (same meaning as the old column)."""
        return sum((item.subtotal for item in self.items.all()), Decimal('0.00'))

    @property
    def grand_total(self):
        return self.total_amount + self.delivery_fee

    # ---- Payment info comes from Payment only -----------------------------
    @property
    def latest_payment(self):
        return self.payments.first()  # Payment.Meta.ordering = ['-created_at']

    @property
    def payment_method(self):
        payment = self.latest_payment
        return payment.payment_method if payment else None

    @property
    def payment_status(self):
        payment = self.latest_payment
        return payment.status if payment else 'PENDING'

    @property
    def is_paid(self):
        return self.payment_status == 'SUCCESS'

    # Keep {{ order.get_payment_method_display }} / get_payment_status_display working in templates.
    def get_payment_method_display(self):
        return dict(PAYMENT_METHOD_CHOICES).get(self.payment_method, '')

    def get_payment_status_display(self):
        payment = self.latest_payment
        return payment.get_status_display() if payment else 'Pending'

    # ---- Rider info for templates that used the old columns ---------------
    @property
    def delivery_person_name(self):
        return self.delivery_partner.name if self.delivery_partner else ""

    @property
    def delivery_person_phone(self):
        return self.delivery_partner.phone if self.delivery_partner else ""

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
    # Snapshot of what the customer actually bought/paid (see module docstring).
    food_name = models.CharField(max_length=150)
    food_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gte=1), name='orderitem_quantity_gte_1'),
        ]

    @property
    def subtotal(self):
        """NORMALIZATION: derived from quantity * food_price, not stored."""
        return self.food_price * self.quantity

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
    PAYMENT_METHOD_CHOICES = PAYMENT_METHOD_CHOICES
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
            date_str = timezone.localdate().strftime("%Y%m%d")
            self.transaction_id = f"PAY-{date_str}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_id} - Order #{self.order.order_number} (₹{self.amount}) [{self.status}]"