import datetime
from django import forms
from django.contrib.auth.models import User
from .models import FoodItem, Category, RestaurantTable, TableReservation, Order, CustomerProfile
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
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_email', 'customer_phone', 'delivery_address', 'delivery_city', 'delivery_notes', 'payment_method']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'placeholder': 'Full Name'}),
            'customer_email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'placeholder': 'Email Address'}),
            'customer_phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'placeholder': '10-digit Phone Number'}),
            'delivery_address': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'rows': 3, 'placeholder': 'Street Address, Apartment/House No.'}),
            'delivery_city': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'placeholder': 'City'}),
            'delivery_notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none', 'rows': 2, 'placeholder': 'Landmarks, buzzer code, food instructions (optional)'}),
            'payment_method': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none bg-white'}),
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
        if res_date and res_date < datetime.date.today():
            raise forms.ValidationError("Reservation date cannot be in the past.")
        return res_date


# Admin Forms
class FoodItemForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = ['name', 'category', 'price', 'description', 'image_url', 'is_veg', 'is_available', 'is_featured', 'preparation_time', 'calories']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none bg-white'}),
            'price': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'rows': 3}),
            'image_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'placeholder': 'https://images.unsplash.com/...'}),
            'preparation_time': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'placeholder': 'e.g. 20-25 mins'}),
            'calories': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'placeholder': 'e.g. 450 kcal'}),
            'is_veg': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-amber-600 rounded'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-amber-600 rounded'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-amber-600 rounded'}),
        }


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


class OrderAdminUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_status', 'payment_status', 'delivery_person_name', 'delivery_person_phone', 'estimated_delivery_time']
        widgets = {
            'order_status': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none bg-white'}),
            'payment_status': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none bg-white'}),
            'delivery_person_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none'}),
            'delivery_person_phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none'}),
            'estimated_delivery_time': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none'}),
        }

    def clean_delivery_person_phone(self):
        phone = self.cleaned_data.get('delivery_person_phone', '')
        return validate_phone_number(phone, required=False)


class ReservationAdminUpdateForm(forms.ModelForm):
    class Meta:
        model = TableReservation
        fields = ['status', 'table', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none bg-white'}),
            'table': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none bg-white'}),
            'admin_notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-amber-500 outline-none', 'rows': 2}),
        }
