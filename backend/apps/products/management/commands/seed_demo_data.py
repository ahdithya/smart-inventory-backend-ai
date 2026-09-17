import datetime
from decimal import Decimal
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import BusinessProfile, User
from apps.categories.models import Category
from apps.products.models import Product
from apps.sales.models import Sale, SaleItem
from apps.stock.models import StockMovement


class Command(BaseCommand):
    help = "Mengisi database dengan data demo UMKM kopi (Kopi Kita) selama 90 hari terakhir."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Hapus data transaksi, produk, dan kategori lama sebelum seeding.",
        )

    def handle(self, *args, **options):
        random.seed(42)
        clean = options.get("clean", False)

        self.stdout.write(self.style.NOTICE("Memulai proses seeding data demo UMKM kopi..."))

        with transaction.atomic():
            if clean:
                self.stdout.write("Membersihkan data transaksi lama...")
                SaleItem.objects.all().delete()
                Sale.objects.all().delete()
                StockMovement.objects.all().delete()
                Product.objects.all().delete()
                Category.objects.all().delete()

            # 1. Akun Pengguna & Profil Bisnis
            owner, _ = User.objects.get_or_create(
                username="owner",
                defaults={
                    "email": "owner@kopikita.id",
                    "role": User.Role.OWNER,
                    "first_name": "Budi",
                    "last_name": "Santoso",
                },
            )
            owner.role = User.Role.OWNER
            owner.set_password("ownerpass123")
            owner.save()

            staff, _ = User.objects.get_or_create(
                username="staff",
                defaults={
                    "email": "staff@kopikita.id",
                    "role": User.Role.STAFF,
                    "first_name": "Siti",
                    "last_name": "Rahma",
                },
            )
            staff.role = User.Role.STAFF
            staff.set_password("staffpass123")
            staff.save()

            BusinessProfile.objects.update_or_create(
                owner=owner,
                defaults={
                    "business_name": "Kopi Kita",
                    "business_type": BusinessProfile.BusinessType.BEVERAGE,
                    "address": "Jl. Senopati No. 12, Jakarta Selatan",
                    "phone": "081234567890",
                },
            )

            # 2. Kategori
            categories_data = [
                ("Espresso Based", "Minuman kopi berbasis espresso mesin"),
                ("Manual Brew", "Kopi seduh manual single origin nusantara"),
                ("Cold Brew & Bottled", "Kopi cold brew kemasan botol siap saji"),
                ("Non-Coffee", "Minuman non-kopi seperti cokelat, matcha, dan taro"),
                ("Tea & Tisane", "Teh premium dan seduhan bunga/herbal"),
                ("Pastry & Bakery", "Kue, roti, dan pastry pendamping kopi"),
                ("Food & Snacks", "Makanan berat dan camilan gurih"),
                ("Coffee Beans (250g)", "Biji kopi sangrai kemasan 250 gram"),
            ]
            category_objs = {}
            for name, desc in categories_data:
                cat, _ = Category.objects.get_or_create(
                    name=name, defaults={"description": desc}
                )
                category_objs[name] = cat

            # 3. Katalog Produk (52 produk)
            catalog = [
                # (category, name, unit, purchase, selling, min, safety, lead, is_seasonal, is_bestseller)
                # Espresso Based (14)
                ("Espresso Based", "Espresso Single", "cup", 4000, 15000, 10, 5, 2, False, False),
                ("Espresso Based", "Espresso Double", "cup", 6000, 20000, 10, 5, 2, False, False),
                ("Espresso Based", "Americano Hot", "cup", 5000, 22000, 15, 8, 3, False, True),
                ("Espresso Based", "Americano Iced", "cup", 6000, 25000, 20, 10, 3, False, True),
                ("Espresso Based", "Caffe Latte Hot", "cup", 8000, 28000, 15, 8, 3, False, True),
                ("Espresso Based", "Caffe Latte Iced", "cup", 9000, 30000, 25, 12, 3, False, True),
                ("Espresso Based", "Cappuccino Hot", "cup", 8000, 28000, 15, 8, 3, False, False),
                ("Espresso Based", "Cappuccino Iced", "cup", 9000, 30000, 15, 8, 3, False, False),
                ("Espresso Based", "Flat White", "cup", 9000, 30000, 10, 5, 3, False, False),
                ("Espresso Based", "Kopi Susu Gula Aren", "cup", 8000, 22000, 30, 15, 2, False, True),
                ("Espresso Based", "Kopi Susu Pandan", "cup", 9000, 25000, 20, 10, 2, False, True),
                ("Espresso Based", "Mocha Hot", "cup", 11000, 32000, 10, 5, 3, False, False),
                ("Espresso Based", "Mocha Iced", "cup", 12000, 35000, 15, 8, 3, False, False),
                ("Espresso Based", "Caramel Macchiato", "cup", 12000, 35000, 15, 8, 3, False, False),

                # Manual Brew (6)
                ("Manual Brew", "V60 Aceh Gayo", "cup", 12000, 32000, 10, 5, 4, False, False),
                ("Manual Brew", "V60 Toraja Sapan", "cup", 13000, 34000, 10, 5, 4, False, False),
                ("Manual Brew", "V60 Bali Kintamani", "cup", 12000, 32000, 10, 5, 4, False, False),
                ("Manual Brew", "Japanese Iced Drip", "cup", 14000, 36000, 12, 6, 4, False, True),
                ("Manual Brew", "Aeropress Single Origin", "cup", 11000, 30000, 8, 4, 3, False, False),
                ("Manual Brew", "French Press Blend", "cup", 10000, 28000, 8, 4, 3, False, False),

                # Cold Brew & Bottled (5)
                ("Cold Brew & Bottled", "Classic Cold Brew Black", "botol", 12000, 30000, 15, 8, 3, False, True),
                ("Cold Brew & Bottled", "Cold Brew White Creamy", "botol", 14000, 35000, 15, 8, 3, False, True),
                ("Cold Brew & Bottled", "Cold Brew Salted Caramel", "botol", 15000, 38000, 12, 6, 3, True, False),
                ("Cold Brew & Bottled", "Cold Brew Peach Blossom", "botol", 16000, 40000, 10, 5, 3, True, False),
                ("Cold Brew & Bottled", "Kopi Susu Literan 1L", "botol", 35000, 85000, 10, 5, 2, False, True),

                # Non-Coffee (7)
                ("Non-Coffee", "Signature Chocolate Hot", "cup", 10000, 28000, 15, 8, 3, False, False),
                ("Non-Coffee", "Signature Chocolate Iced", "cup", 11000, 30000, 20, 10, 3, False, True),
                ("Non-Coffee", "Matcha Latte Hot", "cup", 13000, 32000, 15, 8, 4, False, False),
                ("Non-Coffee", "Matcha Latte Iced", "cup", 14000, 35000, 20, 10, 4, False, True),
                ("Non-Coffee", "Hojicha Latte", "cup", 13000, 33000, 10, 5, 4, False, False),
                ("Non-Coffee", "Red Velvet Velvetine", "cup", 10000, 28000, 12, 6, 3, False, False),
                ("Non-Coffee", "Taro Milkshake", "cup", 10000, 28000, 12, 6, 3, False, False),

                # Tea & Tisane (5)
                ("Tea & Tisane", "Earl Grey Royal Tea", "cup", 5000, 20000, 10, 5, 3, False, False),
                ("Tea & Tisane", "Chamomile Mint Calm", "cup", 6000, 22000, 8, 4, 3, False, False),
                ("Tea & Tisane", "Lemon Iced Tea Fresh", "cup", 5000, 20000, 15, 8, 2, False, True),
                ("Tea & Tisane", "Lychee Iced Tea Special", "cup", 8000, 26000, 18, 9, 2, False, True),
                ("Tea & Tisane", "Peach Iced Tea Garden", "cup", 8000, 26000, 15, 8, 2, False, False),

                # Pastry & Bakery (7)
                ("Pastry & Bakery", "Butter Croissant", "pcs", 10000, 22000, 12, 6, 2, False, True),
                ("Pastry & Bakery", "Almond Croissant", "pcs", 14000, 28000, 10, 5, 2, False, True),
                ("Pastry & Bakery", "Pain au Chocolat", "pcs", 12000, 25000, 10, 5, 2, False, False),
                ("Pastry & Bakery", "Cinnamon Roll Glaze", "pcs", 11000, 24000, 10, 5, 2, False, False),
                ("Pastry & Bakery", "Fudgy Chocolate Brownies", "pcs", 9000, 20000, 15, 8, 2, False, True),
                ("Pastry & Bakery", "Banana Bread Toasted", "pcs", 8000, 18000, 10, 5, 2, False, False),
                ("Pastry & Bakery", "Cheese Danish Puff", "pcs", 12000, 26000, 8, 4, 2, False, False),

                # Food & Snacks (5)
                ("Food & Snacks", "French Fries Truffle Oil", "porsi", 12000, 28000, 15, 8, 3, False, True),
                ("Food & Snacks", "Crispy Chicken Wings (6pcs)", "porsi", 18000, 38000, 12, 6, 3, False, True),
                ("Food & Snacks", "Cireng Crispy Bumbu Rujak", "porsi", 7000, 18000, 15, 8, 2, False, True),
                ("Food & Snacks", "Nasi Goreng Spesial Kopi Kita", "porsi", 16000, 36000, 10, 5, 2, False, False),
                ("Food & Snacks", "Spaghetti Aglio Olio Smoked Beef", "porsi", 18000, 42000, 10, 5, 3, False, False),

                # Coffee Beans (3)
                ("Coffee Beans (250g)", "House Blend Espresso Roast 250g", "bag", 45000, 85000, 8, 4, 5, False, False),
                ("Coffee Beans (250g)", "Single Origin Aceh Gayo 250g", "bag", 55000, 105000, 6, 3, 5, False, False),
                ("Coffee Beans (250g)", "Single Origin Flores Bajawa 250g", "bag", 52000, 98000, 6, 3, 5, False, False),
            ]

            product_objs = []
            seasonal_products = []
            bestseller_products = []

            for idx, item in enumerate(catalog, start=1):
                cat_name, name, unit, p_price, s_price, min_s, safe_s, lead_d, is_season, is_best = item
                sku = f"PROD-{idx:04d}"
                prod, _ = Product.objects.get_or_create(
                    sku=sku,
                    defaults={
                        "category": category_objs[cat_name],
                        "created_by": owner,
                        "name": name,
                        "unit": unit,
                        "purchase_price": Decimal(str(p_price)),
                        "selling_price": Decimal(str(s_price)),
                        "min_stock": min_s,
                        "safety_stock": safe_s,
                        "lead_time_days": lead_d,
                        "current_stock": 0,
                        "is_active": True,
                    },
                )
                product_objs.append(prod)
                if is_season:
                    seasonal_products.append(prod)
                if is_best:
                    bestseller_products.append(prod)

            self.stdout.write(f"Berhasil menyiapkan {len(product_objs)} produk.")

            # 4. Stok Awal & Re-stok Bertahap
            today = timezone.localdate()
            start_simulation_date = today - datetime.timedelta(days=89)

            # Inflow stok awal 90 hari lalu
            stock_movements = []
            for prod in product_objs:
                base_stock = 300 if prod in bestseller_products else 150
                stock_movements.append(
                    StockMovement(
                        product=prod,
                        user=owner,
                        type=StockMovement.Type.IN,
                        qty=base_stock,
                        movement_date=start_simulation_date,
                        note="Stok awal pembukaan toko",
                    )
                )
                prod.current_stock += base_stock

            # Re-stok bertahap di hari ke-60 dan hari ke-30 lalu
            for days_ago in [60, 30]:
                restock_date = today - datetime.timedelta(days=days_ago)
                for prod in product_objs:
                    add_qty = 250 if prod in bestseller_products else 100
                    stock_movements.append(
                        StockMovement(
                            product=prod,
                            user=staff,
                            type=StockMovement.Type.IN,
                            qty=add_qty,
                            movement_date=restock_date,
                            note=f"Pengiriman supplier rutin ({restock_date.strftime('%B %Y')})",
                        )
                    )
                    prod.current_stock += add_qty

            StockMovement.objects.bulk_create(stock_movements)

            # 5. Simulasi Penjualan 90 Hari
            self.stdout.write("Membuat simulasi transaksi penjualan 90 hari...")
            sales_to_create = []
            sale_items_to_create = []
            users = [staff, staff, staff, owner]  # 75% diinput staff, 25% owner

            for day_offset in range(89, -1, -1):
                sale_date = today - datetime.timedelta(days=day_offset)
                is_weekend = sale_date.weekday() in (5, 6)

                # Pola: Weekday lebih ramai (14-22 transaksi), Weekend (5-10 transaksi)
                num_transactions = random.randint(5, 10) if is_weekend else random.randint(14, 22)

                for _ in range(num_transactions):
                    trans_user = random.choice(users)
                    num_items = random.choices([1, 2, 3, 4], weights=[40, 35, 18, 7])[0]

                    # Pilih produk berdasarkan probabilitas
                    chosen_products = set()
                    while len(chosen_products) < num_items:
                        dice = random.random()
                        if dice < 0.50 and bestseller_products:
                            p = random.choice(bestseller_products)
                        elif dice < 0.70 and seasonal_products:
                            p = random.choice(seasonal_products)
                        else:
                            p = random.choice(product_objs)
                        chosen_products.add(p)

                    items_info = []
                    total_amount = Decimal("0.00")

                    for p in chosen_products:
                        # Qty per item transaksi (1-3)
                        qty = random.choices([1, 2, 3], weights=[70, 22, 8])[0]
                        subtotal = p.selling_price * qty
                        total_amount += subtotal
                        items_info.append((p, qty, p.selling_price))
                        p.current_stock -= qty

                    sale = Sale(
                        user=trans_user,
                        sale_date=sale_date,
                        total=total_amount,
                    )
                    sales_to_create.append((sale, items_info))

            # Batch insert sales
            created_sales = Sale.objects.bulk_create([s[0] for s in sales_to_create])
            for sale_obj, items_info in zip(created_sales, [s[1] for s in sales_to_create]):
                for p, qty, price in items_info:
                    sale_items_to_create.append(
                        SaleItem(
                            sale=sale_obj,
                            product=p,
                            qty=qty,
                            unit_price=price,
                        )
                    )

            SaleItem.objects.bulk_create(sale_items_to_create)

            # 6. Kalibrasi Status Stok Akhir untuk Visualisasi Dashboard & Restock
            # Atur ~42 produk Aman, ~6 produk Menipis, ~4 produk Kritis
            self.stdout.write("Mengatur kalibrasi stok akhir (Aman / Menipis / Kritis)...")

            # 4 Produk Kritis (habis)
            critical_candidates = product_objs[-4:]
            for p in critical_candidates:
                p.current_stock = 0

            # 6 Produk Menipis (stok di bawah / sama dengan min_stock)
            low_candidates = product_objs[-10:-4]
            for p in low_candidates:
                p.current_stock = max(1, p.min_stock - random.randint(1, 4))

            # Sisa produk: Aman (di atas min_stock)
            safe_candidates = product_objs[:-10]
            for p in safe_candidates:
                if p.current_stock <= p.min_stock:
                    p.current_stock = p.min_stock + random.randint(15, 60)

            # Simpan seluruh current_stock produk
            Product.objects.bulk_update(product_objs, ["current_stock"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Selesai! Berhasil seeding:\n"
                f"- {len(categories_data)} Kategori\n"
                f"- {len(product_objs)} Produk\n"
                f"- {len(created_sales)} Transaksi Penjualan (90 hari)\n"
                f"- {len(sale_items_to_create)} Detail Item Terjual\n"
                f"- Login Demo: 'owner' / 'ownerpass123' & 'staff' / 'staffpass123'"
            )
        )
