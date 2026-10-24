import datetime
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Category, FoodItem, RestaurantTable, TableReservation, Order, OrderItem, CustomerProfile, Payment


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


