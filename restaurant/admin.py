from django.contrib import admin
from .models import Category, FoodItem, RestaurantTable, TableReservation, Order, OrderItem, CustomerProfile, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('food_name', 'food_price', 'quantity', 'subtotal')


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('transaction_id', 'payment_method', 'amount', 'status', 'payment_gateway', 'paid_at', 'created_at')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_veg', 'is_available', 'is_featured', 'preparation_time')
    list_filter = ('category', 'is_veg', 'is_available', 'is_featured')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_available', 'is_featured')


@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'capacity', 'location', 'is_active')
    list_filter = ('location', 'is_active')
    search_fields = ('table_number',)


@admin.register(TableReservation)
class TableReservationAdmin(admin.ModelAdmin):
    list_display = ('reservation_code', 'customer_name', 'customer_phone', 'reservation_date', 'reservation_time', 'guest_count', 'table', 'status')
    list_filter = ('status', 'reservation_date')
    search_fields = ('reservation_code', 'customer_name', 'customer_phone', 'customer_email')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'customer_phone', 'total_amount', 'payment_method', 'payment_status', 'order_status', 'created_at')
    list_filter = ('order_status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_phone')
    inlines = [OrderItemInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order', 'amount', 'payment_method', 'status', 'payment_gateway', 'paid_at', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('transaction_id', 'order__order_number', 'order__customer_name', 'gateway_reference')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city')
    search_fields = ('user__username', 'phone', 'city')
