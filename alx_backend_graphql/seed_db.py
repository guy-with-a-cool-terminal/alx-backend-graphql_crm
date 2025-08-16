# seed_db.py
"""
Database seeding script for the CRM system.

This script creates sample data to test our GraphQL implementation.
Run with: python manage.py shell < seed_db.py
"""

from crm.models import Customer, Product, Order

print("Clearing existing data...")
Order.objects.all().delete()
Product.objects.all().delete()
Customer.objects.all().delete()

# Create sample customers
print("Creating customers...")
customers = [
    Customer.objects.create(
        name="Alice Johnson",
        email="alice@example.com",
        phone="+1234567890"
    ),
    Customer.objects.create(
        name="Bob Smith",
        email="bob@example.com",
        phone="123-456-7890"
    ),
    Customer.objects.create(
        name="Carol Williams",
        email="carol@example.com"
    ),
]

# Create sample products
print("Creating products...")
products = [
    Product.objects.create(
        name="Laptop",
        price=999.99,
        stock=10,
        description="High-performance laptop"
    ),
    Product.objects.create(
        name="Mouse",
        price=25.50,
        stock=50,
        description="Wireless mouse"
    ),
    Product.objects.create(
        name="Keyboard",
        price=75.00,
        stock=25,
        description="Mechanical keyboard"
    ),
]

# Create sample orders
print("Creating orders...")
order1 = Order.objects.create(
    customer=customers[0],  # Alice
    total_amount=0  # We'll calculate this
)
order1.products.set([products[0], products[1]])  # Laptop + Mouse
order1.total_amount = sum(p.price for p in order1.products.all())
order1.save()

order2 = Order.objects.create(
    customer=customers[1],  # Bob
    total_amount=0
)
order2.products.set([products[1], products[2]])  # Mouse + Keyboard
order2.total_amount = sum(p.price for p in order2.products.all())
order2.save()

print(f"Created {Customer.objects.count()} customers")
print(f"Created {Product.objects.count()} products")
print(f"Created {Order.objects.count()} orders")
print("Database seeded successfully!")
