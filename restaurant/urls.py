from django.urls import path
from . import views

urlpatterns = [
    # Public & Customer routes
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('food/<int:pk>/', views.food_detail, name='food_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:pk>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    path('order/<str:order_number>/invoice/', views.order_invoice, name='order_invoice'),
    path('order/<str:order_number>/kitchen-slip/', views.order_kitchen_slip, name='order_kitchen_slip'),
    path('my-orders/', views.order_history, name='order_history'),
    
    # Table Reservation
    path('table-reservation/', views.table_reservation, name='table_reservation'),
    path('my-reservations/', views.reservation_history, name='reservation_history'),
    path('reservation/cancel/<str:reservation_code>/', views.cancel_reservation, name='cancel_reservation'),
    
    # Customer Auth & Account
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Restaurant Admin Management Portal
    path('portal/', views.admin_dashboard, name='admin_dashboard'),
    path('portal/foods/', views.admin_food_list, name='admin_food_list'),
    path('portal/foods/add/', views.admin_food_add, name='admin_food_add'),
    path('portal/foods/<int:pk>/edit/', views.admin_food_edit, name='admin_food_edit'),
    path('portal/foods/<int:pk>/delete/', views.admin_food_delete, name='admin_food_delete'),
    path('portal/categories/', views.admin_category_list, name='admin_category_list'),
    path('portal/categories/<int:pk>/delete/', views.admin_category_delete, name='admin_category_delete'),
    path('portal/orders/', views.admin_order_list, name='admin_order_list'),
    path('portal/orders/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),
    path('portal/reservations/', views.admin_reservation_list, name='admin_reservation_list'),
    path('portal/reservations/<int:pk>/status/<str:status>/', views.admin_reservation_update_status, name='admin_reservation_update_status'),
    path('portal/customers/', views.admin_customer_list, name='admin_customer_list'),
    path('portal/reports/', views.admin_reports, name='admin_reports'),
]
