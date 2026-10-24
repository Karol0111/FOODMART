import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from django.contrib.auth.models import User

from django.utils import timezone

from .models import (
    Category, FoodItem, RestaurantTable,
    TableReservation, Order, OrderItem, CustomerProfile, Payment
)
from .forms import (
    CustomerRegistrationForm, CustomerProfileForm,
    OrderCheckoutForm, TableReservationForm,
    FoodItemForm, CategoryForm, RestaurantTableForm,
    OrderAdminUpdateForm, ReservationAdminUpdateForm
)


# Helper check for staff/admin
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ==========================================
# PUBLIC / CUSTOMER VIEWS
# ==========================================

def home(request):
    categories = Category.objects.filter(is_active=True)[:6]
    featured_items = FoodItem.objects.filter(is_available=True, is_featured=True)[:8]
    if not featured_items.exists():
        featured_items = FoodItem.objects.filter(is_available=True)[:8]
    
    total_food_count = FoodItem.objects.filter(is_available=True).count()
    tables = RestaurantTable.objects.filter(is_active=True)

    context = {
        'categories': categories,
        'featured_items': featured_items,
        'total_food_count': total_food_count,
        'tables': tables,
    }
    return render(request, 'restaurant/home.html', context)


def menu(request):
    categories = Category.objects.filter(is_active=True)
    items = FoodItem.objects.filter(is_available=True)

    # Search query
    query = request.GET.get('q', '').strip()
    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))

    # Category filter
    category_slug = request.GET.get('category', '')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        items = items.filter(category=selected_category)

    # Diet filter (veg / non-veg)
    diet = request.GET.get('diet', '')
    if diet == 'veg':
        items = items.filter(is_veg=True)
    elif diet == 'non-veg':
        items = items.filter(is_veg=False)

    # Sort order
    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        items = items.order_by('price')
    elif sort == 'price_desc':
        items = items.order_by('-price')
    elif sort == 'name':
        items = items.order_by('name')

    context = {
        'categories': categories,
        'items': items,
        'selected_category': selected_category,
        'search_query': query,
        'selected_diet': diet,
        'selected_sort': sort,
    }
    return render(request, 'restaurant/menu.html', context)


def food_detail(request, pk):
    item = get_object_or_404(FoodItem, pk=pk)
    related_items = FoodItem.objects.filter(category=item.category, is_available=True).exclude(pk=item.pk)[:4]
    return render(request, 'restaurant/food_detail.html', {'item': item, 'related_items': related_items})


# ==========================================
# CART SYSTEM (SESSION-BASED)
# ==========================================

def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    subtotal = Decimal('0.00')

    for item_id, item_data in cart.items():
        price = Decimal(str(item_data.get('price', 0)))
        qty = int(item_data.get('quantity', 1))
        item_total = price * qty
        subtotal += item_total
        cart_items.append({
            'id': item_id,
            'name': item_data.get('name'),
            'price': price,
            'image_url': item_data.get('image_url'),
            'is_veg': item_data.get('is_veg', True),
            'quantity': qty,
            'total': item_total,
        })

    delivery_fee = Decimal('30.00') if cart_items else Decimal('0.00')
    grand_total = subtotal + delivery_fee

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'grand_total': grand_total,
    }
    return render(request, 'restaurant/cart.html', context)


def add_to_cart(request, pk):
    item = get_object_or_404(FoodItem, pk=pk)
    qty = int(request.POST.get('quantity', 1)) if request.method == 'POST' else 1
    if qty < 1:
        qty = 1

    cart = request.session.get('cart', {})
    item_id_str = str(item.id)

    if item_id_str in cart:
        cart[item_id_str]['quantity'] += qty
    else:
        cart[item_id_str] = {
            'name': item.name,
            'price': str(item.price),
            'image_url': item.image_url,
            'is_veg': item.is_veg,
            'quantity': qty,
        }

    request.session['cart'] = cart
    messages.success(request, f"Added {item.name} to your cart!")

    # Check if AJAX or return to referer
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': sum(int(x['quantity']) for x in cart.values()),
            'message': f"Added {item.name} to cart"
        })

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'cart'
    return redirect(next_url)


def update_cart(request, pk):
    cart = request.session.get('cart', {})
    item_id_str = str(pk)
    action = request.POST.get('action')

    if item_id_str in cart:
        if action == 'increase':
            cart[item_id_str]['quantity'] += 1
        elif action == 'decrease':
            cart[item_id_str]['quantity'] -= 1
            if cart[item_id_str]['quantity'] <= 0:
                del cart[item_id_str]
        elif action == 'remove':
            del cart[item_id_str]

    request.session['cart'] = cart
    return redirect('cart')


def remove_from_cart(request, pk):
    cart = request.session.get('cart', {})
    item_id_str = str(pk)
    if item_id_str in cart:
        del cart[item_id_str]
        request.session['cart'] = cart
        messages.info(request, "Item removed from cart.")
    return redirect('cart')


def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart']
        messages.info(request, "Cart cleared.")
    return redirect('cart')


# ==========================================
# CHECKOUT & ORDER TRACKING
# ==========================================

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Your cart is empty. Please add items before checking out.")
        return redirect('menu')

    # Calculate totals
    subtotal = Decimal('0.00')
    for item_data in cart.values():
        subtotal += Decimal(str(item_data.get('price', 0))) * int(item_data.get('quantity', 1))
    delivery_fee = Decimal('30.00')
    grand_total = subtotal + delivery_fee

    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OrderCheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_amount = subtotal
            order.delivery_fee = delivery_fee
            
            # Payment simulation
            if order.payment_method in ['CARD', 'UPI']:
                order.payment_status = 'PAID'
            else:
                order.payment_status = 'PENDING'
            
            order.order_status = 'CONFIRMED'
            order.save()

            # Record payment transaction in Payment table
            p_status = 'SUCCESS' if order.payment_status == 'PAID' else 'PENDING'
            p_gateway = 'UPI Payment Gateway' if order.payment_method == 'UPI' else ('Credit/Debit Card' if order.payment_method == 'CARD' else 'Cash on Delivery')
            Payment.objects.create(
                order=order,
                payment_method=order.payment_method,
                amount=order.grand_total,
                status=p_status,
                payment_gateway=p_gateway,
                paid_at=timezone.now() if p_status == 'SUCCESS' else None
            )

            # Create OrderItems
            for item_id, item_data in cart.items():
                food_item = FoodItem.objects.filter(pk=item_id).first()
                price = Decimal(str(item_data.get('price', 0)))
                qty = int(item_data.get('quantity', 1))
                OrderItem.objects.create(
                    order=order,
                    food_item=food_item,
                    food_name=item_data.get('name'),
                    food_price=price,
                    quantity=qty,
                    subtotal=price * qty
                )

            # Update customer profile address if blank
            if not profile.phone and order.customer_phone:
                profile.phone = order.customer_phone
            if not profile.address and order.delivery_address:
                profile.address = order.delivery_address
            if not profile.city and order.delivery_city:
                profile.city = order.delivery_city
            profile.save()

            # Clear cart
            del request.session['cart']
            messages.success(request, f"Order #{order.order_number} placed successfully!")
            return redirect('order_detail', order_number=order.order_number)
    else:
        initial_data = {
            'customer_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'customer_email': request.user.email,
            'customer_phone': profile.phone,
            'delivery_address': profile.address,
            'delivery_city': profile.city or 'City Center',
        }
        form = OrderCheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart': cart,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'grand_total': grand_total,
    }
    return render(request, 'restaurant/checkout.html', context)


def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    # Allow access if user is staff or is the order owner or if anonymous placed just now
    if not request.user.is_staff and order.user and order.user != request.user:
        messages.error(request, "You are not authorized to view this order.")
        return redirect('home')

    context = {
        'order': order,
        'items': order.items.all(),
        'payment': order.payments.first(),
    }
    return render(request, 'restaurant/order_detail.html', context)


def order_invoice(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    # Allow access if user is staff or is the order owner or if anonymous placed just now
    if not request.user.is_staff and order.user and order.user != request.user:
        messages.error(request, "You are not authorized to view this invoice.")
        return redirect('home')

    context = {
        'order': order,
        'items': order.items.all(),
        'payment': order.payments.first(),
    }
    return render(request, 'restaurant/invoice.html', context)


def order_kitchen_slip(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related('items__food_item__category'), order_number=order_number)
    # Allow access if user is staff or is the order owner
    if not request.user.is_staff and order.user and order.user != request.user:
        messages.error(request, "You are not authorized to view this kitchen slip.")
        return redirect('home')

    items = order.items.select_related('food_item', 'food_item__category').all()
    total_qty = sum(item.quantity for item in items)
    veg_count = sum(item.quantity for item in items if item.food_item and item.food_item.is_veg)
    non_veg_count = total_qty - veg_count

    context = {
        'order': order,
        'items': items,
        'total_qty': total_qty,
        'dish_types_count': items.count(),
        'veg_count': veg_count,
        'non_veg_count': non_veg_count,
        'payment': order.payments.first(),
    }
    return render(request, 'restaurant/kitchen_slip.html', context)


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'restaurant/order_history.html', {'orders': orders})


# ==========================================
# TABLE RESERVATION
# ==========================================

def table_reservation(request):
    tables = RestaurantTable.objects.filter(is_active=True)

    if request.method == 'POST':
        form = TableReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            if request.user.is_authenticated:
                reservation.user = request.user
            reservation.status = 'PENDING'
            reservation.save()
            messages.success(request, f"Table reservation requested! Booking Code: {reservation.reservation_code}. We will confirm shortly.")
            if request.user.is_authenticated:
                return redirect('reservation_history')
            else:
                return render(request, 'restaurant/reservation_success.html', {'reservation': reservation})
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['customer_name'] = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            initial_data['customer_email'] = request.user.email
            if hasattr(request.user, 'profile'):
                initial_data['customer_phone'] = request.user.profile.phone
        initial_data['reservation_date'] = datetime.date.today()
        form = TableReservationForm(initial=initial_data)

    context = {
        'form': form,
        'tables': tables,
    }
    return render(request, 'restaurant/table_reservation.html', context)


@login_required
def reservation_history(request):
    reservations = TableReservation.objects.filter(user=request.user).order_by('-reservation_date', '-reservation_time')
    return render(request, 'restaurant/reservation_history.html', {'reservations': reservations})


@login_required
def cancel_reservation(request, reservation_code):
    reservation = get_object_or_404(TableReservation, reservation_code=reservation_code, user=request.user)
    if reservation.status in ['PENDING', 'CONFIRMED']:
        reservation.status = 'CANCELLED'
        reservation.save()
        messages.info(request, f"Reservation {reservation.reservation_code} has been cancelled.")
    else:
        messages.warning(request, f"Cannot cancel reservation with status: {reservation.status}.")
    return redirect('reservation_history')


# ==========================================
# USER AUTHENTICATION & PROFILE
# ==========================================

def user_register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.set_password(form.cleaned_data['password'])
            user.save()
            # Create CustomerProfile
            CustomerProfile.objects.create(
                user=user,
                phone=form.cleaned_data.get('phone', ''),
            )
            login(request, user)
            messages.success(request, f"Welcome to FoodMart, {user.first_name or user.username}! Your account was created successfully.")
            return redirect('home')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'restaurant/auth/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                if user.is_staff:
                    return redirect('admin_dashboard')
                return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'restaurant/auth/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


@login_required
def profile_view(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = CustomerProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })

    recent_orders = Order.objects.filter(user=request.user)[:5]
    recent_reservations = TableReservation.objects.filter(user=request.user)[:5]

    context = {
        'form': form,
        'recent_orders': recent_orders,
        'recent_reservations': recent_reservations,
    }
    return render(request, 'restaurant/profile.html', context)


# ==========================================
# RESTAURANT / ADMIN MANAGEMENT MODULE
# ==========================================

@user_passes_test(is_admin, login_url='login')
def admin_dashboard(request):
    today = datetime.date.today()
    
    # Financial and order KPIs
    total_revenue = Order.objects.filter(order_status='DELIVERED').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    all_revenue = Order.objects.exclude(order_status='CANCELLED').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(order_status__in=['PENDING', 'CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY']).count()
    today_orders = Order.objects.filter(created_at__date=today).count()
    
    # Reservations KPIs
    today_reservations = TableReservation.objects.filter(reservation_date=today).count()
    pending_reservations = TableReservation.objects.filter(status='PENDING').count()
    
    # Catalog KPIs
    total_dishes = FoodItem.objects.count()
    total_customers = User.objects.filter(is_staff=False).count()

    # Recent items
    recent_orders = Order.objects.all()[:6]
    upcoming_reservations = TableReservation.objects.filter(reservation_date__gte=today).order_by('reservation_date', 'reservation_time')[:5]

    # Quick status counts for chart
    status_counts = {
        'Pending': Order.objects.filter(order_status='PENDING').count(),
        'Preparing': Order.objects.filter(order_status__in=['CONFIRMED', 'PREPARING']).count(),
        'Out For Delivery': Order.objects.filter(order_status='OUT_FOR_DELIVERY').count(),
        'Delivered': Order.objects.filter(order_status='DELIVERED').count(),
        'Cancelled': Order.objects.filter(order_status='CANCELLED').count(),
    }

    context = {
        'total_revenue': total_revenue,
        'all_revenue': all_revenue,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'today_orders': today_orders,
        'today_reservations': today_reservations,
        'pending_reservations': pending_reservations,
        'total_dishes': total_dishes,
        'total_customers': total_customers,
        'recent_orders': recent_orders,
        'upcoming_reservations': upcoming_reservations,
        'status_counts': status_counts,
    }
    return render(request, 'restaurant/admin_portal/dashboard.html', context)


# Food items management
@user_passes_test(is_admin, login_url='login')
def admin_food_list(request):
    category_id = request.GET.get('category')
    diet = request.GET.get('diet')
    query = request.GET.get('q', '').strip()

    items = FoodItem.objects.all()
    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id:
        items = items.filter(category_id=category_id)
    if diet == 'veg':
        items = items.filter(is_veg=True)
    elif diet == 'non-veg':
        items = items.filter(is_veg=False)

    categories = Category.objects.all()
    context = {
        'items': items,
        'categories': categories,
        'selected_category': category_id,
        'selected_diet': diet,
        'query': query,
    }
    return render(request, 'restaurant/admin_portal/food_list.html', context)


@user_passes_test(is_admin, login_url='login')
def admin_food_add(request):
    if request.method == 'POST':
        form = FoodItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f"Added dish '{item.name}' successfully.")
            return redirect('admin_food_list')
    else:
        form = FoodItemForm()
    return render(request, 'restaurant/admin_portal/food_form.html', {'form': form, 'title': 'Add New Food Item'})


@user_passes_test(is_admin, login_url='login')
def admin_food_edit(request, pk):
    item = get_object_or_404(FoodItem, pk=pk)
    if request.method == 'POST':
        form = FoodItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated dish '{item.name}' successfully.")
            return redirect('admin_food_list')
    else:
        form = FoodItemForm(instance=item)
    return render(request, 'restaurant/admin_portal/food_form.html', {'form': form, 'title': f"Edit Dish: {item.name}", 'item': item})


@user_passes_test(is_admin, login_url='login')
def admin_food_delete(request, pk):
    item = get_object_or_404(FoodItem, pk=pk)
    name = item.name
    item.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'message': f"Deleted dish '{name}'.",
            'item_name': name,
            'type': 'delete'
        })
    messages.success(request, f"Deleted dish '{name}'.")
    return redirect('admin_food_list')


# Category management
@user_passes_test(is_admin, login_url='login')
def admin_category_list(request):
    categories = Category.objects.annotate(item_count=Count('food_items'))
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New category added!")
            return redirect('admin_category_list')
    else:
        form = CategoryForm()

    context = {
        'categories': categories,
        'form': form,
    }
    return render(request, 'restaurant/admin_portal/category_list.html', context)


@user_passes_test(is_admin, login_url='login')
def admin_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    name = category.name
    category.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'message': f"Deleted category '{name}'.",
            'item_name': name,
            'type': 'delete'
        })
    messages.success(request, f"Deleted category '{name}'.")
    return redirect('admin_category_list')


# Customer Orders management & Delivery
@user_passes_test(is_admin, login_url='login')
def admin_order_list(request):
    status = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()

    orders = Order.objects.all()
    if status:
        orders = orders.filter(order_status=status)
    if query:
        orders = orders.filter(
            Q(order_number__icontains=query) |
            Q(customer_name__icontains=query) |
            Q(customer_phone__icontains=query)
        )

    context = {
        'orders': orders,
        'selected_status': status,
        'query': query,
    }
    return render(request, 'restaurant/admin_portal/order_list.html', context)


@user_passes_test(is_admin, login_url='login')
def admin_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderAdminUpdateForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save()
            if order.payment_status == 'PAID':
                payment = order.payments.first()
                if payment and payment.status != 'SUCCESS':
                    payment.status = 'SUCCESS'
                    if not payment.paid_at:
                        payment.paid_at = timezone.now()
                    payment.save()
            messages.success(request, f"Order #{order.order_number} status updated to {order.get_order_status_display()}!")
            return redirect('admin_order_detail', pk=order.pk)
    else:
        form = OrderAdminUpdateForm(instance=order)

    context = {
        'order': order,
        'items': order.items.all(),
        'form': form,
    }
    return render(request, 'restaurant/admin_portal/order_detail.html', context)


# Table reservation management
@user_passes_test(is_admin, login_url='login')
def admin_reservation_list(request):
    status = request.GET.get('status', '')
    date = request.GET.get('date', '')

    reservations = TableReservation.objects.all()
    if status:
        reservations = reservations.filter(status=status)
    if date:
        reservations = reservations.filter(reservation_date=date)

    context = {
        'reservations': reservations,
        'selected_status': status,
        'selected_date': date,
    }
    return render(request, 'restaurant/admin_portal/reservation_list.html', context)


@user_passes_test(is_admin, login_url='login')
def admin_reservation_update_status(request, pk, status):
    reservation = get_object_or_404(TableReservation, pk=pk)
    if status in ['CONFIRMED', 'CANCELLED', 'COMPLETED']:
        reservation.status = status
        reservation.save()
        messages.success(request, f"Reservation {reservation.reservation_code} marked as {status}!")
    return redirect('admin_reservation_list')


# Customer Directory
@user_passes_test(is_admin, login_url='login')
def admin_customer_list(request):
    customers = User.objects.filter(is_staff=False).annotate(
        order_count=Count('orders'),
        reservation_count=Count('reservations')
    ).order_by('-date_joined')

    return render(request, 'restaurant/admin_portal/customer_list.html', {'customers': customers})


# Reports & Analytics
@user_passes_test(is_admin, login_url='login')
def admin_reports(request):
    total_sales = Order.objects.filter(order_status='DELIVERED').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_orders_count = Order.objects.count()
    completed_orders = Order.objects.filter(order_status='DELIVERED').count()
    cancelled_orders = Order.objects.filter(order_status='CANCELLED').count()
    
    # Top 5 most ordered dishes
    top_dishes = OrderItem.objects.values('food_name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_qty')[:5]

    # Category breakdown
    category_sales = OrderItem.objects.filter(food_item__isnull=False).values(
        'food_item__category__name'
    ).annotate(
        items_sold=Sum('quantity'),
        revenue=Sum('subtotal')
    ).order_by('-revenue')

    # Payment method breakdown
    payment_breakdown = Order.objects.values('payment_method').annotate(count=Count('id'))

    context = {
        'total_sales': total_sales,
        'total_orders_count': total_orders_count,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'top_dishes': top_dishes,
        'category_sales': category_sales,
        'payment_breakdown': payment_breakdown,
    }
    return render(request, 'restaurant/admin_portal/reports.html', context)
