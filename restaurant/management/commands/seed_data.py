import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from restaurant.models import (
    Category, FoodItem, RestaurantTable,
    TableReservation, Order, OrderItem, CustomerProfile, Payment
)


class Command(BaseCommand):
    help = "Seed database with initial categories, food items, tables, demo users, orders, and reservations."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset dynamic data (reservations, orders, payments) and refresh with current dates and accurate totals'
        )

    def handle(self, *args, **options):
        reset_mode = options.get('reset', False)
        self.stdout.write(self.style.NOTICE(f"Seeding FoodMart data (reset={reset_mode})..."))

        # 1. Create Admin User
        admin_user, admin_created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@foodmart.com",
                "first_name": "FoodMart",
                "last_name": "Manager",
                "is_staff": True,
                "is_superuser": True,
            }
        )
        if admin_created:
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / admin123"))
        else:
            self.stdout.write("Admin user already exists.")

        # 2. Create Customer User & Profile
        customer_user, customer_created = User.objects.get_or_create(
            username="customer",
            defaults={
                "email": "customer@gmail.com",
                "first_name": "Rahul",
                "last_name": "Sharma",
            }
        )
        if customer_created:
            customer_user.set_password("customer123")
            customer_user.save()
            self.stdout.write(self.style.SUCCESS("Created customer user: customer / customer123"))
        else:
            self.stdout.write("Customer user already exists.")

        # Always ensure customer profile exists (even if user already existed)
        cust_profile, prof_created = CustomerProfile.objects.get_or_create(
            user=customer_user,
            defaults={
                "phone": "+91 98765 12345",
                "address": "Flat 402, Sunshine Heights, MG Road",
                "city": "Mumbai",
            }
        )
        if prof_created:
            self.stdout.write(self.style.SUCCESS("Created profile for customer user."))

        # 3. Create Categories (with unique beverages image)
        categories_data = [
            {
                "name": "Starters & Appetizers",
                "icon": "fa-bowl-food",
                "description": "Crispy, savory, and flavorful starters to kickstart your feast.",
                "image_url": "https://images.unsplash.com/photo-1541544741938-0af808871cc0?auto=format&fit=crop&w=600&q=80"
            },
            {
                "name": "Main Course",
                "icon": "fa-utensils",
                "description": "Rich curries, fragrant biryanis, and sizzling entrees crafted by master chefs.",
                "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=600&q=80"
            },
            {
                "name": "Pizzas & Burgers",
                "icon": "fa-pizza-slice",
                "description": "Wood-fired artisanal pizzas and gourmet loaded smash burgers.",
                "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&q=80"
            },
            {
                "name": "Desserts & Sweets",
                "icon": "fa-ice-cream",
                "description": "Indulgent cakes, molten lava delights, and authentic traditional sweets.",
                "image_url": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?auto=format&fit=crop&w=600&q=80"
            },
            {
                "name": "Beverages & Drinks",
                "icon": "fa-martini-glass-citrus",
                "description": "Chilled coolers, exotic mocktails, and fresh natural fruit smoothies.",
                "image_url": "https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=600&q=80"
            },
        ]

        cat_map = {}
        cats_created = 0
        for c in categories_data:
            cat_obj, c_created = Category.objects.get_or_create(
                name=c["name"],
                defaults={
                    "icon": c["icon"],
                    "description": c["description"],
                    "image_url": c["image_url"],
                    "is_active": True,
                }
            )
            # Update image if it was pointing to duplicate or stale URL
            if cat_obj.image_url != c["image_url"]:
                cat_obj.image_url = c["image_url"]
                cat_obj.save()
            cat_map[c["name"]] = cat_obj
            if c_created:
                cats_created += 1

        self.stdout.write(self.style.SUCCESS(f"Categories verified: {len(categories_data)} total ({cats_created} newly created)."))

        # 4. Create Food Items
        food_items_data = [
            # Starters
            {
                "category": "Starters & Appetizers",
                "name": "Paneer Tikka Platter",
                "description": "Cottage cheese cubes marinated in spiced yogurt and grilled in traditional clay tandoor with bell peppers.",
                "price": Decimal("260.00"),
                "image_url": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=600&q=80",
                "is_veg": True,
                "is_featured": True,
                "preparation_time": "15-20 mins",
                "calories": "320 kcal",
            },
            {
                "category": "Starters & Appetizers",
                "name": "Crispy Chilli Chicken",
                "description": "Crisp fried tender chicken bites tossed in fiery garlic, soy glaze, spring onions, and green chillies.",
                "price": Decimal("290.00"),
                "image_url": "https://images.unsplash.com/photo-1562967914-608f82629710?auto=format&fit=crop&w=600&q=80",
                "is_veg": False,
                "is_featured": True,
                "preparation_time": "18-22 mins",
                "calories": "410 kcal",
            },
            {
                "category": "Starters & Appetizers",
                "name": "Loaded Nachos Grande",
                "description": "Crisp corn tortilla chips topped with melted Mexican cheese blend, guacamole, sour cream, and jalapeños.",
                "price": Decimal("220.00"),
                "image_url": "https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?auto=format&fit=crop&w=600&q=80",
                "is_veg": True,
                "is_featured": False,
                "preparation_time": "12-15 mins",
                "calories": "380 kcal",
            },

            # Main Course
            {
                "category": "Main Course",
                "name": "Royal Butter Chicken",
                "description": "Smoked shredded chicken cooked in a rich, creamy tomato gravy infused with fenugreek and butter.",
                "price": Decimal("380.00"),
                "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=600&q=80",
                "is_veg": False,
                "is_featured": True,
                "preparation_time": "25-30 mins",
                "calories": "520 kcal",
            },
            {
                "category": "Main Course",
                "name": "Hyderabadi Dum Biryani",
                "description": "Long-grain basmati rice layered with aromatic spices and saffron, slow cooked to perfection in sealed earthen handi.",
                "price": Decimal("340.00"),
                "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=600&q=80",
                "is_veg": False,
                "is_featured": True,
                "preparation_time": "25-30 mins",
                "calories": "590 kcal",
            },
            {
                "category": "Main Course",
                "name": "Paneer Butter Masala",
                "description": "Succulent cubes of fresh cottage cheese simmered in smooth velvet tomato-cashew curry.",
                "price": Decimal("310.00"),
                "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=600&q=80",
                "is_veg": True,
                "is_featured": True,
                "preparation_time": "20-25 mins",
                "calories": "460 kcal",
            },
            {
                "category": "Main Course",
                "name": "Dal Makhani Special",
                "description": "Slow-simmered black lentils and red kidney beans cooked overnight with butter and fresh cream.",
                "price": Decimal("240.00"),
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80",
                "is_veg": True,
                "is_featured": False,
                "preparation_time": "15-20 mins",
                "calories": "350 kcal",
            },

            # Pizzas & Burgers
            {
                "category": "Pizzas & Burgers",
                "name": "Artisanal Margherita Pizza",
                "description": "San Marzano tomato base, fresh buffalo mozzarella, extra virgin olive oil, and fragrant basil leaves.",
                "price": Decimal("320.00"),
                "image_url": "https://images.unsplash.com/photo-1604382355076-af4b0eb60143?auto=format&fit=crop&w=600&q=80",
                "is_veg": True,
                "is_featured": True,
                "preparation_time": "18-22 mins",
                "calories": "650 kcal",
            },
            {
                "category": "Pizzas & Burgers",
                "name": "Spicy Peri-Peri Chicken Pizza",
                "description": "Fire-roasted spiced chicken chunks, bell peppers, jalapeños, and mozzarella drizzled with peri-peri glaze.",
                "price": Decimal("390.00"),
                "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=600&q=80",
                "is_veg": False,
                "is_featured": True,
                "preparation_time": "20-25 mins",
                "calories": "740 kcal",
            },
            {
                "category": "Pizzas & Burgers",
                "name": "Classic Gourmet Cheeseburger",
                "description": "Juicy grilled patty topped with aged cheddar, caramelized onions, crisp lettuce, and signature truffle mayo.",
                "price": Decimal("250.00"),
                "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80",
                "is_veg": False,
                "is_featured": False,
                "preparation_time": "15-18 mins",
                "calories": "580 kcal",
            },

            # Desserts
            {
                "category": "Desserts & Sweets",
                "name": "Belgian Molten Chocolate Cake",
                "description": "Decadent warm chocolate sponge with a warm oozing chocolate core, served with vanilla bean ice cream.",
                "price": Decimal("190.00"),
                "image_url": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=600&q=80",
                "is_veg": True,
                "is_featured": True,
                "preparation_time": "10-15 mins",
                "calories": "420 kcal",
            },
            {
                "category": "Desserts & Sweets",
                "name": "New York Baked Cheesecake",
                "description": "Silky cream cheese filling on buttery graham crust, glazed with wild strawberry coulis.",
                "price": Decimal("210.00"),
                "image_url": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=600&q=80",
                "is_veg": True,
                "is_featured": False,
                "preparation_time": "5-10 mins",
                "calories": "390 kcal",
            },
            {
                "category": "Desserts & Sweets",
                "name": "Warm Gulab Jamun with Rabri",
                "description": "Golden khoya dumplings steeped in rose-cardamom syrup, crowned with creamy reduced milk rabri and pistachios.",
                "price": Decimal("160.00"),
                "image_url": "https://images.unsplash.com/photo-1589119908995-c6837fa14d48?auto=format&fit=crop&w=600&q=80",
                "is_veg": True,
                "is_featured": False,
                "preparation_time": "8-10 mins",
                "calories": "310 kcal",
            },

            # Beverages
            {
                "category": "Beverages & Drinks",
                "name": "Fresh Mint Mojito",
                "description": "Crushed garden mint, freshly squeezed lime wedges, cane sugar, and chilled sparkling soda.",
                "price": Decimal("130.00"),
                "image_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=600&q=80",
                "is_veg": True,
                "is_featured": False,
                "preparation_time": "5 mins",
                "calories": "110 kcal",
            },
            {
                "category": "Beverages & Drinks",
                "name": "Mango Alphonso Smoothie",
                "description": "Pure Alphonso mango pulp blended with Greek yogurt, honey, and crushed ice.",
                "price": Decimal("150.00"),
                "image_url": "https://images.unsplash.com/photo-1553530666-ba11a7da3888?auto=format&fit=crop&w=600&q=80",
                "is_veg": True,
                "is_featured": True,
                "preparation_time": "5-7 mins",
                "calories": "180 kcal",
            },
            {
                "category": "Beverages & Drinks",
                "name": "Cold Brew Hazelnut Latte",
                "description": "Slow-steeped Arabica coffee cold brew with hazelnut infusion and whole milk over rock ice.",
                "price": Decimal("170.00"),
                "image_url": "https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?auto=format&fit=crop&w=600&q=80",
                "is_veg": True,
                "is_featured": False,
                "preparation_time": "5 mins",
                "calories": "140 kcal",
            },
        ]

        items_created = 0
        items_dict = {}
        for item in food_items_data:
            cat_obj = cat_map[item["category"]]
            f_obj, f_created = FoodItem.objects.get_or_create(
                name=item["name"],
                defaults={
                    "category": cat_obj,
                    "description": item["description"],
                    "price": item["price"],
                    "image_url": item["image_url"],
                    "is_veg": item["is_veg"],
                    "is_featured": item["is_featured"],
                    "is_available": True,
                    "preparation_time": item["preparation_time"],
                    "calories": item["calories"],
                }
            )
            items_dict[item["name"]] = f_obj
            if f_created:
                items_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Food items verified: {len(food_items_data)} total ({items_created} newly created, {len(food_items_data) - items_created} existing)."
        ))

        # 5. Create Restaurant Tables
        tables_data = [
            {"table_number": "T-01", "capacity": 2, "location": "Window View"},
            {"table_number": "T-02", "capacity": 2, "location": "Romantic Booth"},
            {"table_number": "T-03", "capacity": 4, "location": "Main Dining Hall"},
            {"table_number": "T-04", "capacity": 4, "location": "Main Dining Hall"},
            {"table_number": "T-05", "capacity": 6, "location": "Outdoor Garden Terrace"},
            {"table_number": "T-06", "capacity": 6, "location": "Outdoor Garden Terrace"},
            {"table_number": "T-07", "capacity": 8, "location": "Family Lounge"},
            {"table_number": "T-08", "capacity": 10, "location": "Family Lounge"},
        ]

        table_objs = []
        for t in tables_data:
            t_obj, _ = RestaurantTable.objects.get_or_create(
                table_number=t["table_number"],
                defaults={"capacity": t["capacity"], "location": t["location"], "is_active": True}
            )
            table_objs.append(t_obj)

        self.stdout.write(self.style.SUCCESS(f"Created/verified {len(tables_data)} restaurant dining tables."))

        # 6. Create or Reset Sample Orders
        if reset_mode:
            self.stdout.write(self.style.WARNING("Reset mode active: removing old demo orders..."))
            Order.objects.all().delete()

        # Check and repair existing orders if their total_amount doesn't match item subtotals
        existing_orders = Order.objects.all()
        for ord_obj in existing_orders:
            actual_subtotal = ord_obj.items.aggregate(s=Sum('subtotal'))['s']
            if actual_subtotal is not None and actual_subtotal > Decimal('0.00') and ord_obj.total_amount != actual_subtotal:
                self.stdout.write(f"Reconciling Order #{ord_obj.order_number}: ₹{ord_obj.total_amount} -> ₹{actual_subtotal}")
                ord_obj.total_amount = actual_subtotal
                ord_obj.save()
                if ord_obj.payments.exists():
                    for pay in ord_obj.payments.all():
                        pay.amount = ord_obj.grand_total
                        pay.save()

        # If orders are thin (< 6 orders), seed comprehensive orders covering ALL 6 statuses & 5 categories
        if Order.objects.count() < 6:
            self.stdout.write("Seeding rich sample orders across all statuses and categories...")
            
            orders_specs = [
                # 1. DELIVERED (Rahul Sharma, UPI) - Starters
                {
                    "user": customer_user,
                    "customer_name": "Rahul Sharma",
                    "customer_email": "customer@gmail.com",
                    "customer_phone": "+91 98765 12345",
                    "delivery_address": "Flat 402, Sunshine Heights, MG Road",
                    "delivery_city": "Mumbai",
                    "delivery_notes": "Leave with security at main gate",
                    "payment_method": "UPI",
                    "payment_status": "PAID",
                    "order_status": "DELIVERED",
                    "delivery_person_name": "Vikram Singh",
                    "delivery_person_phone": "+91 98111 22334",
                    "estimated_delivery_time": "Delivered in 28 mins",
                    "items": [
                        ("Paneer Tikka Platter", 1),
                        ("Crispy Chilli Chicken", 1),
                    ]
                },
                # 2. DELIVERED (Neha Kapoor, CARD) - Main Course & Dessert
                {
                    "user": None,
                    "customer_name": "Neha Kapoor",
                    "customer_email": "neha.k@example.com",
                    "customer_phone": "+91 98234 56789",
                    "delivery_address": "Penthouse 18B, Ocean Towers, Worli",
                    "delivery_city": "Mumbai",
                    "delivery_notes": "Call on arrival",
                    "payment_method": "CARD",
                    "payment_status": "PAID",
                    "order_status": "DELIVERED",
                    "delivery_person_name": "Rohan Deshmukh",
                    "delivery_person_phone": "+91 98333 44556",
                    "estimated_delivery_time": "Delivered in 35 mins",
                    "items": [
                        ("Royal Butter Chicken", 1),
                        ("Dal Makhani Special", 1),
                        ("Belgian Molten Chocolate Cake", 1),
                    ]
                },
                # 3. OUT_FOR_DELIVERY (Rahul Sharma, CARD) - Pizzas
                {
                    "user": customer_user,
                    "customer_name": "Rahul Sharma",
                    "customer_email": "customer@gmail.com",
                    "customer_phone": "+91 98765 12345",
                    "delivery_address": "Flat 402, Sunshine Heights, MG Road",
                    "delivery_city": "Mumbai",
                    "delivery_notes": "Ring doorbell twice",
                    "payment_method": "CARD",
                    "payment_status": "PAID",
                    "order_status": "OUT_FOR_DELIVERY",
                    "delivery_person_name": "Aman Gupta",
                    "delivery_person_phone": "+91 98222 33445",
                    "estimated_delivery_time": "10 - 15 mins away",
                    "items": [
                        ("Spicy Peri-Peri Chicken Pizza", 1),
                        ("Artisanal Margherita Pizza", 1),
                    ]
                },
                # 4. PREPARING (Priya Patel, COD) - Starters & Beverages
                {
                    "user": None,
                    "customer_name": "Priya Patel",
                    "customer_email": "priya@example.com",
                    "customer_phone": "+91 99887 76655",
                    "delivery_address": "B-12, Green Park Avenue",
                    "delivery_city": "Mumbai",
                    "delivery_notes": "Extra spicy please, less ice in mojito",
                    "payment_method": "COD",
                    "payment_status": "PENDING",
                    "order_status": "PREPARING",
                    "delivery_person_name": "FoodMart Express Rider",
                    "delivery_person_phone": "+91 98765 43210",
                    "estimated_delivery_time": "25 - 30 mins",
                    "items": [
                        ("Loaded Nachos Grande", 1),
                        ("Fresh Mint Mojito", 2),
                    ]
                },
                # 5. CONFIRMED (Amit Joshi, UPI) - Burgers & Dessert
                {
                    "user": None,
                    "customer_name": "Amit Joshi",
                    "customer_email": "amit.j@example.com",
                    "customer_phone": "+91 97654 32109",
                    "delivery_address": "Tower 4, Apt 803, Silver Palms, Andheri East",
                    "delivery_city": "Mumbai",
                    "delivery_notes": "Door code #4088",
                    "payment_method": "UPI",
                    "payment_status": "PAID",
                    "order_status": "CONFIRMED",
                    "delivery_person_name": "FoodMart Express Rider",
                    "delivery_person_phone": "+91 98765 43210",
                    "estimated_delivery_time": "35 - 40 mins",
                    "items": [
                        ("Classic Gourmet Cheeseburger", 2),
                        ("New York Baked Cheesecake", 1),
                    ]
                },
                # 6. PENDING (Sneha Kulkarni, COD) - Biryani & Coffee
                {
                    "user": None,
                    "customer_name": "Sneha Kulkarni",
                    "customer_email": "sneha.k@example.com",
                    "customer_phone": "+91 98112 34567",
                    "delivery_address": "House 45, Gulmohar Colony, Juhu",
                    "delivery_city": "Mumbai",
                    "delivery_notes": "Hot packaging needed",
                    "payment_method": "COD",
                    "payment_status": "PENDING",
                    "order_status": "PENDING",
                    "delivery_person_name": "FoodMart Express Rider",
                    "delivery_person_phone": "+91 98765 43210",
                    "estimated_delivery_time": "40 - 45 mins",
                    "items": [
                        ("Hyderabadi Dum Biryani", 1),
                        ("Cold Brew Hazelnut Latte", 1),
                    ]
                },
                # 7. CANCELLED (Rohan Mehta, COD) - Indian Curry & Dessert
                {
                    "user": None,
                    "customer_name": "Rohan Mehta",
                    "customer_email": "rohan.m@example.com",
                    "customer_phone": "+91 98999 88877",
                    "delivery_address": "Flat 101, Sea View Residency, Bandra",
                    "delivery_city": "Mumbai",
                    "delivery_notes": "Cancelled by customer due to sudden travel",
                    "payment_method": "COD",
                    "payment_status": "FAILED",
                    "order_status": "CANCELLED",
                    "delivery_person_name": "",
                    "delivery_person_phone": "",
                    "estimated_delivery_time": "Cancelled",
                    "items": [
                        ("Paneer Butter Masala", 1),
                        ("Warm Gulab Jamun with Rabri", 2),
                    ]
                },
            ]

            for spec in orders_specs:
                order = Order.objects.create(
                    user=spec["user"],
                    customer_name=spec["customer_name"],
                    customer_email=spec["customer_email"],
                    customer_phone=spec["customer_phone"],
                    delivery_address=spec["delivery_address"],
                    delivery_city=spec["delivery_city"],
                    delivery_notes=spec["delivery_notes"],
                    total_amount=Decimal("0.00"),  # Computed dynamically below
                    delivery_fee=Decimal("30.00"),
                    payment_method=spec["payment_method"],
                    payment_status=spec["payment_status"],
                    order_status=spec["order_status"],
                    delivery_person_name=spec["delivery_person_name"],
                    delivery_person_phone=spec["delivery_person_phone"],
                    estimated_delivery_time=spec["estimated_delivery_time"],
                )

                for dish_name, qty in spec["items"]:
                    dish_item = items_dict.get(dish_name)
                    if dish_item:
                        OrderItem.objects.create(
                            order=order,
                            food_item=dish_item,
                            food_name=dish_item.name,
                            food_price=dish_item.price,
                            quantity=qty,
                            subtotal=dish_item.price * qty
                        )

                # Exactly compute order total_amount from items
                computed_subtotal = OrderItem.objects.filter(order=order).aggregate(s=Sum("subtotal"))["s"] or Decimal("0.00")
                order.total_amount = computed_subtotal
                order.save()

                # Create Payment record with exact grand total
                p_status = "SUCCESS" if order.payment_status == "PAID" else ("FAILED" if order.order_status == "CANCELLED" else "PENDING")
                p_gateway = "UPI Gateway" if order.payment_method == "UPI" else ("Card Network" if order.payment_method == "CARD" else "Cash on Delivery")
                Payment.objects.create(
                    order=order,
                    payment_method=order.payment_method,
                    amount=order.grand_total,
                    status=p_status,
                    payment_gateway=p_gateway,
                    paid_at=timezone.now() if p_status == "SUCCESS" else None
                )

            self.stdout.write(self.style.SUCCESS(f"Created {len(orders_specs)} verified demo orders with exact item totals and payment records."))

        # 7. Create or Refresh Sample Table Reservations
        today = timezone.localdate()
        tomorrow = today + datetime.timedelta(days=1)
        day_after = today + datetime.timedelta(days=2)

        has_stale_reservations = False
        if TableReservation.objects.exists():
            # Check if all reservations are in the past
            active_count = TableReservation.objects.filter(reservation_date__gte=today).count()
            if active_count == 0:
                has_stale_reservations = True

        if reset_mode or not TableReservation.objects.exists() or has_stale_reservations:
            if reset_mode or has_stale_reservations:
                self.stdout.write(self.style.WARNING("Refreshing stale reservations with current dates..."))
                TableReservation.objects.all().delete()

            TableReservation.objects.create(
                user=customer_user,
                customer_name="Rahul Sharma",
                customer_email="customer@gmail.com",
                customer_phone="+91 98765 12345",
                table=table_objs[1],  # Romantic Booth
                reservation_date=today,
                reservation_time=datetime.time(19, 30),
                guest_count=2,
                special_requests="Anniversary dinner, quiet corner with candlelight please.",
                status="CONFIRMED",
                admin_notes="Table decorated with flowers and complimentary welcome mocktails."
            )
            TableReservation.objects.create(
                user=None,
                customer_name="Sunita Rao",
                customer_email="sunita.rao@example.com",
                customer_phone="+91 98321 65498",
                table=table_objs[2],  # Main Dining Hall
                reservation_date=today,
                reservation_time=datetime.time(13, 0),
                guest_count=4,
                special_requests="Business lunch meeting. Fast service requested.",
                status="COMPLETED",
                admin_notes="Billed and vacated on schedule."
            )
            TableReservation.objects.create(
                user=None,
                customer_name="Aditya Verma",
                customer_email="aditya@example.com",
                customer_phone="+91 98123 45678",
                table=table_objs[4],  # Outdoor Garden Terrace
                reservation_date=tomorrow,
                reservation_time=datetime.time(20, 0),
                guest_count=5,
                special_requests="Family get-together with kids. High chair needed.",
                status="PENDING"
            )
            TableReservation.objects.create(
                user=customer_user,
                customer_name="Karan Kapoor",
                customer_email="karan.k@example.com",
                customer_phone="+91 98450 11223",
                table=table_objs[6],  # Family Lounge
                reservation_date=day_after,
                reservation_time=datetime.time(20, 30),
                guest_count=6,
                special_requests="Birthday cake celebration. Table near music speakers.",
                status="CONFIRMED",
                admin_notes="Pre-booked with 600 advance token."
            )
            self.stdout.write(self.style.SUCCESS("Created/refreshed active table reservations for today and upcoming days."))
        else:
            self.stdout.write("Active table reservations already present.")

        self.stdout.write(self.style.SUCCESS("FoodMart database successfully seeded and verified!"))
