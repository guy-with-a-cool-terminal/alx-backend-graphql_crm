# crm/models.py
"""
CRM Models for the GraphQL Assignment

These models represent the core entities in our Customer Relationship Management system:
- Customer: People who buy from us
- Product: Items we sell
- Order: Purchases made by customers

The assignment requires specific fields and relationships between these models.
"""

from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re

class Customer(models.Model):
    """
    Customer model represents people who buy our products.
    
    Requirements from assignment:
    - name (required)
    - email (required, unique) 
    - phone (optional, with format validation)
    """
    
    name = models.CharField(
        max_length=100, 
        help_text="Customer's full name"
    )
    
    email = models.EmailField(
        unique=True,  # Ensures no duplicate emails (assignment requirement)
        help_text="Customer's email address - must be unique"
    )
    
    # Phone number validation regex - supports formats like +1234567890 or 123-456-7890
    phone_regex = RegexValidator(
        regex=r'^(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}$',
        message="Phone number must be in format: '+1234567890' or '123-456-7890'"
    )
    
    phone = models.CharField(
        validators=[phone_regex], 
        max_length=17,  # Enough for international numbers
        blank=True,     # Optional field as per assignment
        null=True,
        help_text="Optional phone number in format +1234567890 or 123-456-7890"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this customer was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this customer was last updated"
    )
    
    class Meta:
        ordering = ['-created_at']  # Newest customers first
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
    
    def __str__(self):
        """String representation for admin interface and debugging"""
        return f"{self.name} ({self.email})"
    
    def clean(self):
        """Custom validation beyond field-level validation"""
        super().clean()
        
        # Ensure email is properly formatted (additional check)
        if self.email and '@' not in self.email:
            raise ValidationError({'email': 'Please enter a valid email address.'})


class Product(models.Model):
    """
    Product model represents items we sell.
    
    Requirements from assignment:
    - name (required)
    - price (required, positive)
    - stock (optional, non-negative, default 0)
    """
    
    name = models.CharField(
        max_length=200,
        help_text="Product name"
    )
    
    price = models.DecimalField(
        max_digits=10,   # Allows prices up to 99,999,999.99
        decimal_places=2, # Two decimal places for cents
        help_text="Product price - must be positive"
    )
    
    stock = models.PositiveIntegerField(
        default=0,  # Default stock is 0 as per assignment
        help_text="Number of items in stock - cannot be negative"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Optional product description"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this product was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this product was last updated"
    )
    
    class Meta:
        ordering = ['name']  # Alphabetical order by name
        verbose_name = "Product"
        verbose_name_plural = "Products"
    
    def __str__(self):
        """String representation showing name and price"""
        return f"{self.name} (${self.price})"
    
    def clean(self):
        """Custom validation to ensure price is positive"""
        super().clean()
        
        if self.price is not None and self.price <= 0:
            raise ValidationError({'price': 'Price must be positive.'})


class Order(models.Model):
    """
    Order model represents purchases made by customers.
    
    Requirements from assignment:
    - customer_id (required, links to existing customer)
    - product_ids (required, links to products via many-to-many)
    - order_date (optional, defaults to now)
    - total_amount (calculated from product prices)
    """
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,  # If customer is deleted, delete their orders
        related_name='orders',     # Allows customer.orders.all()
        help_text="Customer who placed this order"
    )
    
    # Many-to-many relationship with products
    # One order can have multiple products, one product can be in multiple orders
    products = models.ManyToManyField(
        Product,
        related_name='orders',
        help_text="Products included in this order"
    )
    
    order_date = models.DateTimeField(
        auto_now_add=True,  # Automatically set to now when created
        help_text="When this order was placed"
    )
    
    # We'll calculate this from product prices in our GraphQL mutation
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Total amount for this order (calculated from product prices)"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Optional notes about this order"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this order record was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this order was last updated"
    )
    
    class Meta:
        ordering = ['-order_date']  # Newest orders first
        verbose_name = "Order"
        verbose_name_plural = "Orders"
    
    def __str__(self):
        """String representation showing customer and total"""
        return f"Order by {self.customer.name} - ${self.total_amount}"
    
    def calculate_total(self):
        """
        Calculate total amount from associated products.
        This method will be called in our GraphQL mutation.
        """
        total = sum(product.price for product in self.products.all())
        return total
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically calculate total_amount
        Note: This won't work for many-to-many relationships until after
        the order is saved, so we'll handle this in our GraphQL mutation.
        """
        super().save(*args, **kwargs)


# Additional utility functions for the models

def validate_customer_email_unique(email):
    """
    Utility function to check if email is unique before creating customer.
    Used in GraphQL mutations for validation.
    """
    return not Customer.objects.filter(email=email).exists()

def validate_products_exist(product_ids):
    """
    Utility function to validate that all provided product IDs exist.
    Used in GraphQL mutations for validation.
    """
    existing_count = Product.objects.filter(id__in=product_ids).count()
    return existing_count == len(product_ids)