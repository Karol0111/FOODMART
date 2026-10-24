import datetime
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.utils import timezone
from .forms import FoodItemForm
from .models import (
    Category, FoodItem, RestaurantTable, TableReservation, Order, OrderItem,
    CustomerProfile, Payment, DeliveryPartner,
)


class FoodMartTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.customer = User.objects.create_user(username='testcust', password='password123', email='cust@test.com', first_name='Test', last_name='User')
        CustomerProfile.objects.create(user=self.customer, phone='9876543210', address='123 Test St', city='Testville')

        self.admin = User.objects.create_superuser(username='testadmin', password='password123', email='admin@test.com')

        # Create category and food item
        self.category = Category.objects.create(name='Pizzas', slug='pizzas', icon='fa-pizza-slice', description='Delicious Pizzas')
        self.food = FoodItem.objects.create(
            category=self.category,
            name='Test Pizza',
            description='Cheesy test pizza',
            price=Decimal('299.00'),
            is_veg=True,
            is_available=True,
        )

        # Create table
        self.table = RestaurantTable.objects.create(table_number='T-10', capacity=4, location='Main Dining Hall')

    def test_homepage(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FoodMart')
        self.assertContains(response, 'Test Pizza')

    def test_menu_page_and_filtering(self):
        response = self.client.get(reverse('menu') + '?category=pizzas')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Pizza')

    def test_cart_workflow(self):
        # Add to cart
        response = self.client.post(reverse('add_to_cart', args=[self.food.id]), {'quantity': 2}, follow=True)
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertIn(str(self.food.id), session['cart'])
        self.assertEqual(session['cart'][str(self.food.id)]['quantity'], 2)

        # View cart
        response = self.client.get(reverse('cart'))
        self.assertContains(response, 'Test Pizza')
        self.assertContains(response, '598.00')

    def test_checkout_and_order_tracking(self):
        self.client.login(username='testcust', password='password123')
        # Add to cart first
        self.client.post(reverse('add_to_cart', args=[self.food.id]), {'quantity': 1})
        
        # Post checkout form
        checkout_data = {
            'customer_name': 'Test User',
            'customer_email': 'cust@test.com',
            'customer_phone': '9876543210',
            'delivery_address': '123 Test St',
            'delivery_city': 'Testville',
            'delivery_notes': 'Gate code 1234',
            'payment_method': 'COD',
        }
        response = self.client.post(reverse('checkout'), checkout_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        order = Order.objects.filter(user=self.customer).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().food_name, 'Test Pizza')
        self.assertContains(response, order.order_number)

        # Totals are derived from the items; payment info comes from the Payment row
        self.assertEqual(order.total_amount, Decimal('299.00'))
        self.assertEqual(order.grand_total, Decimal('329.00'))
        self.assertEqual(order.payment_method, 'COD')
        self.assertEqual(order.payment_status, 'PENDING')

        # Verify Payment record creation
        self.assertTrue(order.payments.exists())
        payment = order.payments.first()
        self.assertEqual(payment.amount, order.grand_total)
        self.assertEqual(payment.payment_method, 'COD')
        self.assertTrue(payment.transaction_id.startswith('PAY-'))

        # Test single-page invoice view
        invoice_response = self.client.get(reverse('order_invoice', args=[order.order_number]))
        self.assertEqual(invoice_response.status_code, 200)
        self.assertContains(invoice_response, 'FoodMart')
        self.assertContains(invoice_response, 'TAX INVOICE')
        self.assertContains(invoice_response, payment.transaction_id)
        self.assertContains(invoice_response, 'Test Pizza')

        # Test restructured single-page kitchen slip (KOT) view
        kot_response = self.client.get(reverse('order_kitchen_slip', args=[order.order_number]))
        self.assertEqual(kot_response.status_code, 200)
        self.assertContains(kot_response, 'Kitchen Order Ticket')
        self.assertContains(kot_response, 'KOT')
        self.assertContains(kot_response, 'Test Pizza')
        self.assertContains(kot_response, order.order_number)

    def test_table_reservation(self):
        self.client.login(username='testcust', password='password123')
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        res_data = {
            'customer_name': 'Test User',
            'customer_email': 'cust@test.com',
            'customer_phone': '9876543210',
            'table': self.table.id,
            'reservation_date': tomorrow,
            'reservation_time': '19:00',
            'guest_count': 2,
            'special_requests': 'Anniversary decoration',
        }
        response = self.client.post(reverse('table_reservation'), res_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        res = TableReservation.objects.filter(user=self.customer).first()
        self.assertIsNotNone(res)
        self.assertEqual(res.status, 'PENDING')
        self.assertEqual(res.guest_count, 2)

    def test_admin_portal_access_and_order_update(self):
        # Non-staff user cannot access admin portal
        self.client.login(username='testcust', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

        # Admin user can access
        self.client.login(username='testadmin', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Restaurant Overview')

    def test_registration_valid(self):
        reg_data = {
            'username': 'newuser1',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@foodmart.com',
            'phone': '9876543210',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }
        response = self.client.post(reverse('register'), reg_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser1').exists())
        user = User.objects.get(username='newuser1')
        self.assertEqual(user.email, 'newuser@foodmart.com')

    def test_registration_invalid_email_format(self):
        reg_data = {
            'username': 'bademailuser',
            'first_name': 'Bad',
            'last_name': 'Email',
            'email': 'not-an-email@nodomain',
            'phone': '9876543210',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }
        response = self.client.post(reverse('register'), reg_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='bademailuser').exists())
        self.assertTrue(response.context['form'].has_error('email'))

    def test_registration_duplicate_email(self):
        reg_data = {
            'username': 'dupemailuser',
            'first_name': 'Dup',
            'last_name': 'User',
            'email': 'CUST@TEST.COM',  # Case-insensitive duplicate of cust@test.com
            'phone': '9876543210',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }
        response = self.client.post(reverse('register'), reg_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='dupemailuser').exists())
        self.assertTrue(response.context['form'].has_error('email'))
        self.assertIn('An account with this email address is already registered.', response.context['form'].errors['email'])

    def test_registration_weak_passwords(self):
        weak_passwords = [
            'short1!',          # Too short (< 8 chars)
            'nouppercase123!',  # Missing uppercase
            'NOLOWERCASE123!',  # Missing lowercase
            'NoNumberHere!',    # Missing number
            'NoSpecialChar123', # Missing special char
        ]
        for weak_pwd in weak_passwords:
            reg_data = {
                'username': f'user_{weak_pwd[:5]}',
                'first_name': 'Test',
                'last_name': 'User',
                'email': f'{weak_pwd[:5]}@test.com',
                'phone': '9876543210',
                'password': weak_pwd,
                'confirm_password': weak_pwd,
            }
            response = self.client.post(reverse('register'), reg_data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].has_error('password'))

    def test_registration_password_mismatch(self):
        reg_data = {
            'username': 'mismatchuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'mismatch@test.com',
            'phone': '9876543210',
            'password': 'StrongPass123!',
            'confirm_password': 'DifferentPass123!',
        }
        response = self.client.post(reverse('register'), reg_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'confirm_password', 'Passwords do not match. Please re-enter your confirm password.')

    def test_registration_invalid_phones(self):
        invalid_phones = [
            '12345',               # Too short (< 10 digits)
            '98765abcde',          # Contains letters
            '0000000000',          # All identical digits
            '1111111111',          # All identical digits
            '0987654321',          # 10-digit starting with 0
            '1234567890123456',    # Exceeds 15 digits
        ]
        for bad_phone in invalid_phones:
            reg_data = {
                'username': f'phone_{bad_phone[:4]}',
                'first_name': 'Test',
                'last_name': 'User',
                'email': f'phone_{bad_phone[:4]}@test.com',
                'phone': bad_phone,
                'password': 'StrongPass123!',
                'confirm_password': 'StrongPass123!',
            }
            response = self.client.post(reverse('register'), reg_data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].has_error('phone'))

    def test_registration_valid_international_phones(self):
        valid_phones = [
            '+91 98765 43210',
            '+1 (555) 234-5678',
            '9876543210',
        ]
        for idx, good_phone in enumerate(valid_phones):
            self.client.logout()
            reg_data = {
                'username': f'validphone_{idx}',
                'first_name': 'Test',
                'last_name': 'User',
                'email': f'validphone_{idx}@test.com',
                'phone': good_phone,
                'password': 'StrongPass123!',
                'confirm_password': 'StrongPass123!',
            }
            response = self.client.post(reverse('register'), reg_data, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(User.objects.filter(username=f'validphone_{idx}').exists())

    def test_login_page_no_demo_credentials(self):
        # Ensure login page is accessible and does not expose demo credentials
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Quick Demo Credentials')
        self.assertNotContains(response, 'customer123')
        self.assertNotContains(response, 'admin123')
        self.assertContains(response, 'Enter your username')

        # Successful login test
        login_res = self.client.post(reverse('login'), {'username': 'testcust', 'password': 'password123'}, follow=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(login_res.context['user'].is_authenticated)
        self.assertEqual(login_res.context['user'].username, 'testcust')

    def test_admin_food_delete_ajax(self):
        self.client.login(username='testadmin', password='password123')
        del_item = FoodItem.objects.create(
            category=self.category,
            name='Temporary Dish',
            price=Decimal('150.00'),
            is_available=True,
        )
        response = self.client.post(
            reverse('admin_food_delete', args=[del_item.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['type'], 'delete')
        self.assertIn("Deleted dish 'Temporary Dish'.", data['message'])
        self.assertFalse(FoodItem.objects.filter(id=del_item.id).exists())

    # ==================================================================
    # Tests for the normalized (3NF) schema
    # ==================================================================
    def _make_order(self, status='DELIVERED', lines=((299, 2),), user=None, rider=None, fee='30.00'):
        order = Order.objects.create(
            user=user, customer_name='Order Person', customer_email='o@test.com',
            customer_phone='9876543210', delivery_address='1 Test Road', delivery_city='Testville',
            delivery_fee=Decimal(fee), order_status=status, delivery_partner=rider,
        )
        for price, qty in lines:
            OrderItem.objects.create(
                order=order, food_item=self.food, food_name='Test Pizza',
                food_price=Decimal(str(price)), quantity=qty,
            )
        return order

    def _reservation_data(self, **overrides):
        data = {
            'customer_name': 'Test User', 'customer_email': 'cust@test.com',
            'customer_phone': '9876543210', 'table': self.table.id,
            'reservation_date': (timezone.localdate() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
            'reservation_time': '19:00', 'guest_count': 2, 'special_requests': '',
        }
        data.update(overrides)
        return data

    def test_order_and_item_totals_are_derived(self):
        order = self._make_order(lines=((299, 2), (150, 1)))
        self.assertEqual(sorted(i.subtotal for i in order.items.all()), [Decimal('150.00'), Decimal('598.00')])
        self.assertEqual(order.total_amount, Decimal('748.00'))
        self.assertEqual(order.grand_total, Decimal('778.00'))
        annotated = Order.objects.with_totals().get(pk=order.pk)
        self.assertEqual(annotated.items_total_db, Decimal('748.00'))
        self.assertEqual(annotated.grand_total_db, Decimal('778.00'))

    def test_order_without_items_has_zero_total(self):
        order = self._make_order(lines=())
        self.assertEqual(order.total_amount, Decimal('0.00'))
        self.assertEqual(Order.objects.with_totals().get(pk=order.pk).items_total_db, Decimal('0.00'))

    def test_payment_info_comes_from_payment_table(self):
        order = self._make_order()
        self.assertIsNone(order.payment_method)
        self.assertEqual(order.payment_status, 'PENDING')
        Payment.objects.create(order=order, payment_method='UPI', amount=order.grand_total, status='SUCCESS')
        order = Order.objects.get(pk=order.pk)
        self.assertEqual(order.payment_method, 'UPI')
        self.assertEqual(order.payment_status, 'SUCCESS')
        self.assertTrue(order.is_paid)

    def test_rider_details_live_in_one_delivery_partner_row(self):
        rider = DeliveryPartner.objects.create(name='Ravi', phone='+91 98123 45670')
        first = self._make_order(rider=rider)
        second = self._make_order(rider=rider)
        self.assertEqual(DeliveryPartner.objects.count(), 1)
        self.assertEqual(first.delivery_person_name, 'Ravi')
        self.assertEqual(second.delivery_person_phone, '+91 98123 45670')
        self.assertEqual(rider.orders.count(), 2)

    def test_unassigned_order_has_blank_rider_details(self):
        order = self._make_order()
        self.assertEqual(order.delivery_person_name, '')
        self.assertEqual(order.delivery_person_phone, '')

    def test_checkout_card_marks_payment_success(self):
        self.client.login(username='testcust', password='password123')
        self.client.post(reverse('add_to_cart', args=[self.food.id]), {'quantity': 1})
        self.client.post(reverse('checkout'), {
            'customer_name': 'Test User', 'customer_email': 'cust@test.com',
            'customer_phone': '9876543210', 'delivery_address': '123 Test St',
            'delivery_city': 'Testville', 'delivery_notes': '', 'payment_method': 'CARD',
        })
        order = Order.objects.get(user=self.customer)
        self.assertEqual(order.payment_status, 'SUCCESS')
        self.assertIsNotNone(order.payments.first().paid_at)

    def test_admin_dispatch_updates_rider_and_payment(self):
        self.client.login(username='testadmin', password='password123')
        order = self._make_order(status='OUT_FOR_DELIVERY')
        Payment.objects.create(order=order, payment_method='COD', amount=order.grand_total, status='PENDING')
        data = {
            'order_status': 'DELIVERED', 'payment_status': 'SUCCESS',
            'delivery_person_name': 'Ravi Kumar', 'delivery_person_phone': '9812345670',
            'estimated_delivery_time': 'Delivered in 25 mins',
        }
        response = self.client.post(reverse('admin_order_detail', args=[order.pk]), data)
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'DELIVERED')
        self.assertEqual(order.delivery_partner.name, 'Ravi Kumar')
        payment = order.payments.first()
        self.assertEqual(payment.status, 'SUCCESS')
        self.assertIsNotNone(payment.paid_at)

        # Dispatching a second order with the same rider reuses the same DeliveryPartner row
        other = self._make_order(status='PREPARING')
        data.update({'order_status': 'OUT_FOR_DELIVERY', 'payment_status': 'PENDING'})
        self.client.post(reverse('admin_order_detail', args=[other.pk]), data)
        other.refresh_from_db()
        self.assertEqual(other.delivery_partner_id, order.delivery_partner_id)
        self.assertEqual(DeliveryPartner.objects.count(), 1)

    def test_admin_rider_needs_name_and_phone_together(self):
        self.client.login(username='testadmin', password='password123')
        order = self._make_order(status='PREPARING')
        response = self.client.post(reverse('admin_order_detail', args=[order.pk]), {
            'order_status': 'OUT_FOR_DELIVERY', 'payment_status': 'PENDING',
            'delivery_person_name': 'No Phone', 'delivery_person_phone': '',
            'estimated_delivery_time': '10 mins',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].has_error('delivery_person_phone'))
        order.refresh_from_db()
        self.assertIsNone(order.delivery_partner)

    def test_food_form_stores_typed_prep_time_and_calories(self):
        form = FoodItemForm({
            'name': 'Form Dish', 'category': self.category.id, 'price': '120.00',
            'description': 'Tasty', 'image_url': '', 'is_veg': 'on', 'is_available': 'on',
            'preparation_time': '15-20 mins', 'calories': '320 kcal',
        })
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save()
        self.assertEqual((item.prep_time_min, item.prep_time_max, item.calories_kcal), (15, 20, 320))
        self.assertEqual(item.preparation_time, '15-20 mins')
        self.assertEqual(item.calories, '320 kcal')

    def test_food_form_rejects_bad_prep_time(self):
        base = {'name': 'Bad Dish', 'category': self.category.id, 'price': '10.00', 'description': 'x'}
        for bad in ('soon', '25-20 mins', '9999 mins'):
            form = FoodItemForm({**base, 'preparation_time': bad, 'calories': ''})
            self.assertFalse(form.is_valid(), bad)
            self.assertIn('preparation_time', form.errors)

    def test_reservation_double_booking_is_blocked(self):
        self.client.login(username='testcust', password='password123')
        self.client.post(reverse('table_reservation'), self._reservation_data())
        response = self.client.post(reverse('table_reservation'), self._reservation_data())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertEqual(TableReservation.objects.filter(table=self.table).count(), 1)

    def test_cancelled_booking_frees_the_slot(self):
        self.client.login(username='testcust', password='password123')
        data = self._reservation_data()
        TableReservation.objects.create(
            customer_name='Earlier', customer_email='e@test.com', customer_phone='9876543210',
            table=self.table, reservation_date=data['reservation_date'],
            reservation_time=data['reservation_time'], guest_count=2, status='CANCELLED',
        )
        self.client.post(reverse('table_reservation'), data)
        active = TableReservation.objects.filter(table=self.table).exclude(status='CANCELLED')
        self.assertEqual(active.count(), 1)

    def test_reservation_guest_count_cannot_exceed_table_capacity(self):
        self.client.login(username='testcust', password='password123')
        response = self.client.post(reverse('table_reservation'), self._reservation_data(guest_count=6))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(TableReservation.objects.count(), 0)

    def test_database_blocks_duplicate_active_slot_and_zero_quantity(self):
        slot = dict(
            customer_name='A', customer_email='a@test.com', customer_phone='9876543210',
            table=self.table, reservation_date=timezone.localdate(),
            reservation_time=datetime.time(20, 0), guest_count=2,
        )
        TableReservation.objects.create(status='PENDING', **slot)
        with self.assertRaises(IntegrityError), transaction.atomic():
            TableReservation.objects.create(status='CONFIRMED', **slot)

        order = self._make_order(lines=())
        with self.assertRaises(IntegrityError), transaction.atomic():
            OrderItem.objects.create(order=order, food_name='Zero', food_price=Decimal('10.00'), quantity=0)

    def test_admin_dashboard_and_reports_use_derived_totals(self):
        self.client.login(username='testadmin', password='password123')
        delivered = self._make_order(status='DELIVERED', lines=((299, 2),))            # 598
        self._make_order(status='CANCELLED', lines=((100, 1),))                        # 100
        pending = self._make_order(status='PENDING', lines=((50, 3),))                 # 150
        Payment.objects.create(order=delivered, payment_method='UPI', amount=delivered.grand_total, status='SUCCESS')
        Payment.objects.create(order=pending, payment_method='COD', amount=pending.grand_total, status='PENDING')

        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_revenue'], Decimal('598.00'))
        self.assertEqual(response.context['all_revenue'], Decimal('748.00'))   # cancelled excluded

        response = self.client.get(reverse('admin_reports'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_sales'], Decimal('598.00'))
        top = list(response.context['top_dishes'])
        self.assertEqual(top[0]['food_name'], 'Test Pizza')
        self.assertEqual(top[0]['total_qty'], 6)
        self.assertEqual(top[0]['total_revenue'], Decimal('848.00'))
        methods = {row['payment_method']: row['count'] for row in response.context['payment_breakdown']}
        self.assertEqual(methods, {'UPI': 1, 'COD': 1})

    def test_admin_customer_list_counts_are_not_multiplied(self):
        self.client.login(username='testadmin', password='password123')
        self._make_order(user=self.customer)
        self._make_order(user=self.customer)
        TableReservation.objects.create(
            user=self.customer, customer_name='Test User', customer_email='cust@test.com',
            customer_phone='9876543210', table=self.table,
            reservation_date=timezone.localdate(), reservation_time=datetime.time(18, 0), guest_count=2,
        )
        response = self.client.get(reverse('admin_customer_list'))
        self.assertEqual(response.status_code, 200)
        row = next(c for c in response.context['customers'] if c.pk == self.customer.pk)
        self.assertEqual(row.order_count, 2)
        self.assertEqual(row.reservation_count, 1)