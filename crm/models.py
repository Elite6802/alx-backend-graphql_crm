import uuid
from django.db import models
from decimal import Decimal

# --- Customer Model ---
class Customer(models.Model):
    # Using UUIDs for primary keys is a good practice for modern distributed systems
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, help_text="Email must be unique across all customers.")
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# --- Product Model ---
class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price must be positive.")
    stock = models.IntegerField(default=0, help_text="Stock quantity, cannot be negative.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# --- Order Model ---
class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Customer is a Foreign Key (One-to-Many relationship)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    # Products is a Many-to-Many relationship
    products = models.ManyToManyField('Product', related_name='orders')

    # total_amount is calculated in the mutation logic
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id.hex[:8]} for {self.customer.name}"
