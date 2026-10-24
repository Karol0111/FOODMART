import datetime
import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from restaurant.models import (
    Category, FoodItem, RestaurantTable, TableReservation,
    Order, OrderItem, CustomerProfile, DeliveryPartner, Payment
)


def parse_minutes(text):
    """'15-20 mins' -> (15, 20); '5 mins' -> (5, 5)."""
    nums = [int(n) for n in re.findall(r"\d+", text)]
    return (nums[0], nums[-1]) if nums else (20, 25)


def parse_int(text):
    """'320 kcal' -> 320."""
    m = re.search(r"\d+", text or "")
    return int(m.group()) if m else None


class Command(BaseCommand):
    help = "Seed database with initial categories, food items, tables, demo users, orders, and reservations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Delete demo orders, payments and reservations first so dates/orders are recreated fresh.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding FoodMart data..."))
        if options["reset"]:
            Payment.objects.all().delete()
            Order.objects.all().delete()
            TableReservation.objects.all().delete()
            self.stdout.write("Reset: removed existing orders, payments and reservations.")

        # 1. Create Admin User
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@foodmart.com",
                "first_name": "FoodMart",
                "last_name": "Manager",
                "is_staff": True,
                "is_superuser": True,
            }
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / admin123"))
        else:
            self.stdout.write("Admin user already exists.")

        # 2. Create Customer User
        customer_user, created = User.objects.get_or_create(
            username="customer",
            defaults={
                "email": "customer@gmail.com",
                "first_name": "Rahul",
                "last_name": "Sharma",
            }
        )
        if created:
            customer_user.set_password("customer123")
            customer_user.save()
            CustomerProfile.objects.get_or_create(
                user=customer_user,
                defaults={
                    "phone": "+91 98765 12345",
                    "address": "Flat 402, Sunshine Heights, MG Road",
                    "city": "Mumbai",
                }
            )
            self.stdout.write(self.style.SUCCESS("Created customer user: customer / customer123"))

        # 3. Create Categories
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
                "image_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=600&q=80"
            },
        ]

        cat_map = {}
        for c in categories_data:
            cat_obj, _ = Category.objects.get_or_create(
                name=c["name"],
                defaults={
                    "icon": c["icon"],
                    "description": c["description"],
                    "image_url": c["image_url"],
                    "is_active": True,
                }
            )
            cat_map[c["name"]] = cat_obj

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

        for item in food_items_data:
            cat_obj = cat_map[item["category"]]
            prep_min, prep_max = parse_minutes(item["preparation_time"])
            FoodItem.objects.get_or_create(
                name=item["name"],
                defaults={
                    "category": cat_obj,
                    "description": item["description"],
                    "price": item["price"],
                    "image_url": item["image_url"],
                    "is_veg": item["is_veg"],
                    "is_featured": item["is_featured"],
                    "is_available": True,
                    "prep_time_min": prep_min,
                    "prep_time_max": prep_max,
                    "calories_kcal": parse_int(item["calories"]),
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Ensured {len(food_items_data)} food items across {len(categories_data)} categories."))

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

        self.stdout.write(self.style.SUCCESS(f"Ensured {len(tables_data)} restaurant dining tables."))

        # 6. Delivery partners (rider details live here, not on Order)
        riders = {}
        for name, phone in [
            ("Vikram Singh", "+91 98111 22334"),
            ("Aman Gupta", "+91 98222 33445"),
        ]:
            riders[name], _ = DeliveryPartner.objects.get_or_create(phone=phone, defaults={"name": name})

        # 7. Sample orders. Totals are DERIVED from the items, so they can never disagree.
        def dish(name):
            return FoodItem.objects.get(name=name)

        def make_order(user, name, email, phone, address, notes, status, method, pay_status,
                       lines, rider=None, eta="30 - 45 mins"):
            order = Order.objects.create(
                user=user, customer_name=name, customer_email=email, customer_phone=phone,
                delivery_address=address, delivery_city="Mumbai", delivery_notes=notes,
                order_status=status, delivery_partner=rider, estimated_delivery_time=eta,
            )
            for food, qty in lines:
                OrderItem.objects.create(
                    order=order, food_item=food, food_name=food.name,
                    food_price=food.price, quantity=qty,
                )
            Payment.objects.create(
                order=order, payment_method=method, status=pay_status,
                amount=order.grand_total,
                paid_at=timezone.now() if pay_status == "SUCCESS" else None,
            )
            return order

        if not Order.objects.exists():
            home = "Flat 402, Sunshine Heights, MG Road"
            make_order(customer_user, "Rahul Sharma", "customer@gmail.com", "+91 98765 12345", home,
                       "Leave with security at main gate", "DELIVERED", "UPI", "SUCCESS",
                       [(dish("Paneer Tikka Platter"), 1), (dish("Royal Butter Chicken"), 1)],
                       rider=riders["Vikram Singh"], eta="Delivered in 28 mins")
            make_order(customer_user, "Rahul Sharma", "customer@gmail.com", "+91 98765 12345", home,
                       "Ring doorbell twice", "OUT_FOR_DELIVERY", "CARD", "SUCCESS",
                       [(dish("Loaded Nachos Grande"), 2), (dish("Fresh Mint Mojito"), 2)],
                       rider=riders["Aman Gupta"], eta="10 - 15 mins away")
            make_order(None, "Priya Patel", "priya@example.com", "+91 99887 76655", "B-12, Green Park Avenue",
                       "Extra spicy please", "PREPARING", "COD", "PENDING",
                       [(dish("Hyderabadi Dum Biryani"), 1)], eta="25 - 30 mins")
            make_order(customer_user, "Rahul Sharma", "customer@gmail.com", "+91 98765 12345", home,
                       "", "CONFIRMED", "UPI", "SUCCESS",
                       [(dish("Artisanal Margherita Pizza"), 1), (dish("Mango Alphonso Smoothie"), 1)],
                       eta="35 - 40 mins")
            make_order(None, "Neha Kapoor", "neha@example.com", "+91 98700 11223", "C-7, Lotus Residency",
                       "", "PENDING", "COD", "PENDING",
                       [(dish("Classic Gourmet Cheeseburger"), 2)], eta="30 - 45 mins")
            make_order(None, "Arjun Mehta", "arjun@example.com", "+91 98111 99887", "22, Palm Grove Society",
                       "", "DELIVERED", "CARD", "SUCCESS",
                       [(dish("Belgian Molten Chocolate Cake"), 2), (dish("Paneer Butter Masala"), 1),
                        (dish("Warm Gulab Jamun with Rabri"), 1)],
                       rider=riders["Aman Gupta"], eta="Delivered in 33 mins")
            make_order(None, "Sana Khan", "sana@example.com", "+91 98222 44556", "9, Rose Villa Lane",
                       "Cancelled by customer", "CANCELLED", "CARD", "FAILED",
                       [(dish("Crispy Chilli Chicken"), 1)], eta="")
            self.stdout.write(self.style.SUCCESS("Created 7 demo orders with items and payments."))

        # 8. Sample table reservations (dates are relative to the day you seed; use --reset to refresh)
        if not TableReservation.objects.exists():
            today = timezone.localdate()
            tomorrow = today + datetime.timedelta(days=1)
            TableReservation.objects.create(
                user=customer_user,
                customer_name="Rahul Sharma",
                customer_email="customer@gmail.com",
                customer_phone="+91 98765 12345",
                table=table_objs[1],
                reservation_date=today,
                reservation_time=datetime.time(19, 30),
                guest_count=2,
                special_requests="Anniversary dinner, quiet corner with candlelight please.",
                status="CONFIRMED",
                admin_notes="Table decorated with flowers and complimentary welcome mocktails."
            )
            TableReservation.objects.create(
                user=None,
                customer_name="Aditya Verma",
                customer_email="aditya@example.com",
                customer_phone="+91 98123 45678",
                table=table_objs[4],
                reservation_date=tomorrow,
                reservation_time=datetime.time(20, 0),
                guest_count=5,
                special_requests="Family get-together with kids. High chair needed.",
                status="PENDING"
            )
            TableReservation.objects.create(
                user=None,
                customer_name="Meera Iyer",
                customer_email="meera@example.com",
                customer_phone="+91 98765 00112",
                table=table_objs[2],
                reservation_date=today,
                reservation_time=datetime.time(13, 0),
                guest_count=4,
                status="COMPLETED"
            )
            self.stdout.write(self.style.SUCCESS("Created sample table reservations."))

        self.stdout.write(self.style.SUCCESS("FoodMart database successfully seeded!"))