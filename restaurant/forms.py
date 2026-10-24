import datetime
import re
from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    FoodItem, Category, RestaurantTable, TableReservation, Order, CustomerProfile,
    DeliveryPartner, Payment,
)
from .validators import validate_email_format, validate_unique_email, validate_password_strength, validate_phone_number


class CustomerRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition', 'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition', 'placeholder': 'Email Address'}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition', 'placeholder': 'e.g. 9876543210 or +91 98765 43210', 'id': 'id_phone'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'w-full pl-4 pr-10 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition', 'placeholder': 'Choose Password', 'id': 'id_password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'w-full pl-4 pr-10 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition', 'placeholder': 'Confirm Password', 'id': 'id_confirm_password'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition', 'placeholder': 'Choose a Username'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        normalized_email = validate_email_format(email)
        validate_unique_email(normalized_email)
        return normalized_email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        return validate_phone_number(phone, required=True)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")

        if password:
            temp_user = User(
                username=username or '',
                email=email or '',
                first_name=first_name or '',
                last_name=last_name or '',
            )
            pwd_errors = validate_password_strength(password, user=temp_user)
            for err in pwd_errors:
                self.add_error('password', err)

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match. Please re-enter your confirm password.")

        return cleaned_data


class CustomerProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300'}))

    class Meta:
        model = CustomerProfile
        fields = ['phone', 'address', 'city']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300'}),
            'address': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        normalized_email = validate_email_format(email)
        user_id = self.instance.user_id if (self.instance and self.instance.pk) else None
        validate_unique_email(normalized_email, exclude_user_id=user_id)
        return normalized_email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        return validate_phone_number(phone, required=False)


class OrderCheckoutForm(forms.ModelForm):
    # Not an Order column any more (3NF): the checkout view saves it as a Payment row.
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_METHOD_CHOICES,
        initial='COD',
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none bg-white'}),
    )

    field_order = ['customer_name', 'customer_email', 'customer_phone', 'delivery_address', 'delivery_city', 'delivery_notes', 'payment_method']

    class Meta:
        model = Order
        fields = ['customer_name', 'customer_email', 'customer_phone', 'delivery_address', 'delivery_city', 'delivery_notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'placeholder': 'Full Name'}),
            'customer_email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'placeholder': 'Email Address'}),
            'customer_phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'placeholder': '10-digit Phone Number'}),
            'delivery_address': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'rows': 3, 'placeholder': 'Street Address, Apartment/House No.'}),
            'delivery_city': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'placeholder': 'City'}),
            'delivery_notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'rows': 2, 'placeholder': 'Landmarks, buzzer code, food instructions (optional)'}),
        }

    def clean_customer_email(self):
        email = self.cleaned_data.get('customer_email', '')
        return validate_email_format(email)

    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone', '')
        return validate_phone_number(phone, required=True)


class TableReservationForm(forms.ModelForm):
    class Meta:
        model = TableReservation
        fields = ['customer_name', 'customer_email', 'customer_phone', 'table', 'reservation_date', 'reservation_time', 'guest_count', 'special_requests']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'placeholder': 'Your Full Name'}),
            'customer_email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'placeholder': 'Your Email Address'}),
            'customer_phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'placeholder': 'Contact Number'}),
            'table': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none bg-white'}),
            'reservation_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none'}),
            'reservation_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none'}),
            'guest_count': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'min': 1, 'max': 20}),
            'special_requests': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'rows': 2, 'placeholder': 'Any dietary restrictions, birthday/anniversary decor, quiet spot, etc.'}),
        }

    def clean_customer_email(self):
        email = self.cleaned_data.get('customer_email', '')
        return validate_email_format(email)

    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone', '')
        return validate_phone_number(phone, required=True)

    def clean_reservation_date(self):
        res_date = self.cleaned_data.get('reservation_date')
        if res_date and res_date < timezone.localdate():
            raise forms.ValidationError("Reservation date cannot be in the past.")
        return res_date

    def clean(self):
        cleaned = super().clean()
        table = cleaned.get('table')
        res_date = cleaned.get('reservation_date')
        res_time = cleaned.get('reservation_time')
        if table and res_date and res_time:
            clash = TableReservation.objects.filter(
                table=table, reservation_date=res_date, reservation_time=res_time
            ).exclude(status='CANCELLED')
            if self.instance.pk:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise forms.ValidationError(
                    "That table is already booked for the selected date and time. "
                    "Please choose another table or time."
                )
        return cleaned


# Admin Forms
class FoodItemForm(forms.ModelForm):
    # The admin still types "20-25 mins" / "450 kcal"; they are parsed into the typed columns
    # prep_time_min, prep_time_max and calories_kcal (atomic values, 1NF) on save.
    preparation_time = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'placeholder': 'e.g. 20-25 mins'}),
    )
    calories = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'placeholder': 'e.g. 450 kcal'}),
    )

    field_order = ['name', 'category', 'price', 'description', 'image_url', 'is_veg', 'is_available', 'is_featured', 'preparation_time', 'calories']

    class Meta:
        model = FoodItem
        fields = ['name', 'category', 'price', 'description', 'image_url', 'is_veg', 'is_available', 'is_featured']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none bg-white'}),
            'price': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'rows': 3}),
            'image_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'placeholder': 'https://images.unsplash.com/...'}),
            'is_veg': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-amber-600 rounded'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-amber-600 rounded'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-amber-600 rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial.setdefault('preparation_time', self.instance.preparation_time)
        self.initial.setdefault('calories', self.instance.calories)

    def clean_preparation_time(self):
        text = (self.cleaned_data.get('preparation_time') or '').strip()
        nums = [int(n) for n in re.findall(r'\d+', text)]
        if not nums:
            raise forms.ValidationError("Enter the time in minutes, e.g. 20-25 mins or 15 mins.")
        low, high = nums[0], nums[-1]
        if low > high:
            raise forms.ValidationError("The first number cannot be larger than the second (e.g. 20-25).")
        if high > 600:
            raise forms.ValidationError("Preparation time looks too long (maximum 600 minutes).")
        return (low, high)

    def clean_calories(self):
        text = (self.cleaned_data.get('calories') or '').strip()
        if not text:
            return None
        match = re.search(r'\d+', text)
        if not match:
            raise forms.ValidationError("Enter calories as a number, e.g. 450 kcal.")
        return int(match.group())

    def save(self, commit=True):
        item = super().save(commit=False)
        item.prep_time_min, item.prep_time_max = self.cleaned_data['preparation_time']
        item.calories_kcal = self.cleaned_data['calories']
        if commit:
            item.save()
            self._save_m2m()
        return item


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'icon', 'description', 'image_url', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none'}),
            'icon': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'placeholder': 'fa-burger'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'rows': 2}),
            'image_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-amber-600 rounded'}),
        }


class RestaurantTableForm(forms.ModelForm):
    class Meta:
        model = RestaurantTable
        fields = ['table_number', 'capacity', 'location', 'is_active']
        widgets = {
            'table_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'placeholder': 'T-01'}),
            'capacity': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'min': 1}),
            'location': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none bg-white'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-amber-600 rounded'}),
        }


def _digits(value):
    return re.sub(r'\D', '', value or '')


class OrderAdminUpdateForm(forms.ModelForm):
    # Same field names the admin template already renders, but they no longer map to Order columns:
    #  - payment_status updates the order's Payment row
    #  - delivery_person_name / delivery_person_phone point the order at a DeliveryPartner row
    payment_status = forms.ChoiceField(
        choices=Payment.PAYMENT_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none bg-white'}),
    )
    delivery_person_name = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none'}),
    )
    delivery_person_phone = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none'}),
    )

    field_order = ['order_status', 'payment_status', 'delivery_person_name', 'delivery_person_phone', 'estimated_delivery_time']

    class Meta:
        model = Order
        fields = ['order_status', 'estimated_delivery_time']
        widgets = {
            'order_status': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none bg-white'}),
            'estimated_delivery_time': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial.setdefault('payment_status', self.instance.payment_status)
            self.initial.setdefault('delivery_person_name', self.instance.delivery_person_name)
            self.initial.setdefault('delivery_person_phone', self.instance.delivery_person_phone)

    def clean_delivery_person_phone(self):
        phone = self.cleaned_data.get('delivery_person_phone', '')
        return validate_phone_number(phone, required=False)

    def clean(self):
        cleaned = super().clean()
        name = (cleaned.get('delivery_person_name') or '').strip()
        phone = (cleaned.get('delivery_person_phone') or '').strip()
        if name and not phone and 'delivery_person_phone' not in self.errors:
            self.add_error('delivery_person_phone', "Enter the rider's phone number.")
        if phone and not name:
            self.add_error('delivery_person_name', "Enter the rider's name.")
        return cleaned

    def save(self, commit=True):
        order = super().save(commit=False)
        name = (self.cleaned_data.get('delivery_person_name') or '').strip()
        phone = (self.cleaned_data.get('delivery_person_phone') or '').strip()
        if name and phone:
            # One DeliveryPartner row per rider phone, however the number was typed.
            partner = next((p for p in DeliveryPartner.objects.all() if _digits(p.phone) == _digits(phone)), None)
            if partner is None:
                partner = DeliveryPartner.objects.create(name=name, phone=phone)
            elif partner.name != name:
                partner.name = name
                partner.save(update_fields=['name'])
            order.delivery_partner = partner
        else:
            order.delivery_partner = None
        if commit:
            order.save()
            self.sync_payment(order)
        return order

    def sync_payment(self, order):
        """Payment is the single source of truth for payment status. Call after order.save()."""
        status = self.cleaned_data['payment_status']
        payment = Payment.objects.filter(order=order).first()  # newest first (Meta.ordering)
        if payment is None:
            if status != 'PENDING':
                Payment.objects.create(
                    order=order, payment_method='COD', amount=order.grand_total, status=status,
                    paid_at=timezone.now() if status == 'SUCCESS' else None,
                )
            return
        if payment.status != status:
            payment.status = status
            if status == 'SUCCESS' and not payment.paid_at:
                payment.paid_at = timezone.now()
            payment.save()


class ReservationAdminUpdateForm(forms.ModelForm):
    class Meta:
        model = TableReservation
        fields = ['status', 'table', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none bg-white'}),
            'table': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none bg-white'}),
            'admin_notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'rows': 2}),
        }

    def clean(self):
        cleaned = super().clean()
        table = cleaned.get('table')
        status = cleaned.get('status')
        if table and status and status != 'CANCELLED' and self.instance.pk:
            clash = TableReservation.objects.filter(
                table=table,
                reservation_date=self.instance.reservation_date,
                reservation_time=self.instance.reservation_time,
            ).exclude(status='CANCELLED').exclude(pk=self.instance.pk)
            if clash.exists():
                raise forms.ValidationError(
                    f"Table {table.table_number} already has an active booking at that date and time."
                )
        return cleaned