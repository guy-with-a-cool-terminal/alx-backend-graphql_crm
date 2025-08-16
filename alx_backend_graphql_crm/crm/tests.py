# crm/schema.py
"""
Complete CRM GraphQL Schema - Tasks 1 & 2

This file contains all GraphQL types, queries, and mutations for our CRM system.
We're building on top of the basic "hello" query from Task 0.

Assignment Requirements:
- Create Customer, Product, Order types from Django models
- Implement mutations: CreateCustomer, BulkCreateCustomers, CreateProduct, CreateOrder
- Handle validation and error cases
- Support nested queries (orders with customer and product details)
"""

import graphene
from graphene_django import DjangoObjectType
from graphene import InputObjectType, List, String, Boolean, Field, Int, Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
import re

# Import our Django models
from .models import Customer, Product, Order


# =============================================
# GraphQL Types (convert Django models to GraphQL types)
# =============================================

class CustomerType(DjangoObjectType):
    """
    GraphQL type for Customer model.
    
    DjangoObjectType automatically creates GraphQL fields from Django model fields.
    This saves us from manually defining each field.
    """
    
    class Meta:
        model = Customer
        fields = "__all__"  # Include all fields from the model
        description = "A customer in our CRM system"


class ProductType(DjangoObjectType):
    """
    GraphQL type for Product model.
    """
    
    class Meta:
        model = Product
        fields = "__all__"
        description = "A product we sell"


class OrderType(DjangoObjectType):
    """
    GraphQL type for Order model.
    
    This automatically includes relationships:
    - order.customer will return CustomerType
    - order.products will return List[ProductType]
    """
    
    class Meta:
        model = Order
        fields = "__all__"
        description = "An order placed by a customer"


# =============================================
# Input Types (for mutations)
# =============================================

class CustomerInput(InputObjectType):
    """
    Input type for customer data in mutations.
    
    InputObjectType is used when we want to accept complex objects
    as arguments to mutations, rather than individual fields.
    """
    
    name = String(required=True, description="Customer's full name")
    email = String(required=True, description="Customer's email address")
    phone = String(description="Customer's phone number (optional)")


class ProductInput(InputObjectType):
    """
    Input type for product data in mutations.
    """
    
    name = String(required=True, description="Product name")
    price = Decimal(required=True, description="Product price")
    stock = Int(description="Product stock quantity")
    description = String(description="Product description")


class OrderInput(InputObjectType):
    """
    Input type for order data in mutations.
    """
    
    customer_id = Int(required=True, description="ID of the customer placing the order")
    product_ids = List(Int, required=True, description="List of product IDs in this order")


# =============================================
# Mutations (for creating/updating data)
# =============================================

class CreateCustomer(graphene.Mutation):
    """
    Mutation to create a single customer.
    
    Assignment Requirements:
    - Validate email uniqueness
    - Validate phone format
    - Return created customer and success message
    - Handle validation errors gracefully
    """
    
    class Arguments:
        """Define what arguments this mutation accepts"""
        input = CustomerInput(required=True)
    
    # Define what this mutation returns
    customer = Field(CustomerType, description="The created customer")
    success = Boolean(description="Whether the operation was successful")
    message = String(description="Success or error message")
    errors = List(String, description="List of validation errors")
    
    @staticmethod
    def mutate(root, info, input):
        """
        The actual function that creates the customer.
        
        Parameters:
        - root: The parent object (None for root mutations)
        - info: GraphQL execution context
        - input: The CustomerInput data
        """
        
        errors = []
        
        # Validation 1: Check if email already exists
        if Customer.objects.filter(email=input.email).exists():
            errors.append("Email already exists")
        
        # Validation 2: Check phone format if provided
        if input.phone:
            phone_pattern = r'^(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}$'
            if not re.match(phone_pattern, input.phone):
                errors.append("Invalid phone format. Use +1234567890 or 123-456-7890")
        
        # If there are validation errors, return them
        if errors:
            return CreateCustomer(
                customer=None,
                success=False,
                message="Validation failed",
                errors=errors
            )
        
        try:
            # Create the customer
            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.phone or ""
            )
            
            return CreateCustomer(
                customer=customer,
                success=True,
                message="Customer created successfully",
                errors=[]
            )
            
        except Exception as e:
            return CreateCustomer(
                customer=None,
                success=False,
                message=f"Error creating customer: {str(e)}",
                errors=[str(e)]
            )


class BulkCreateCustomers(graphene.Mutation):
    """
    Mutation to create multiple customers at once.
    
    Assignment Requirements:
    - Accept a list of customer inputs
    - Validate each customer individually
    - Support partial success (create valid ones, report errors for invalid ones)
    - Use database transactions for consistency
    """
    
    class Arguments:
        input = List(CustomerInput, required=True, description="List of customers to create")
    
    # Return created customers and any errors
    customers = List(CustomerType, description="Successfully created customers")
    errors = List(String, description="Errors for customers that couldn't be created")
    success_count = Int(description="Number of customers successfully created")
    
    @staticmethod
    def mutate(root, info, input):
        """Create multiple customers with partial success support"""
        
        created_customers = []
        errors = []
        
        # Process each customer individually
        for i, customer_data in enumerate(input):
            try:
                # Check email uniqueness
                if Customer.objects.filter(email=customer_data.email).exists():
                    errors.append(f"Customer {i+1}: Email {customer_data.email} already exists")
                    continue
                
                # Validate phone if provided
                if customer_data.phone:
                    phone_pattern = r'^(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}$'
                    if not re.match(phone_pattern, customer_data.phone):
                        errors.append(f"Customer {i+1}: Invalid phone format")
                        continue
                
                # Create customer if validation passes
                customer = Customer.objects.create(
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.phone or ""
                )
                created_customers.append(customer)
                
            except Exception as e:
                errors.append(f"Customer {i+1}: {str(e)}")
        
        return BulkCreateCustomers(
            customers=created_customers,
            errors=errors,
            success_count=len(created_customers)
        )


class CreateProduct(graphene.Mutation):
    """
    Mutation to create a product.
    
    Assignment Requirements:
    - Validate price is positive
    - Validate stock is non-negative
    - Return created product
    """
    
    class Arguments:
        input = ProductInput(required=True)
    
    product = Field(ProductType, description="The created product")
    success = Boolean(description="Whether the operation was successful")
    message = String(description="Success or error message")
    errors = List(String, description="List of validation errors")
    
    @staticmethod
    def mutate(root, info, input):
        """Create a new product with validation"""
        
        errors = []
        
        # Validation 1: Price must be positive
        if input.price <= 0:
            errors.append("Price must be positive")
        
        # Validation 2: Stock cannot be negative
        if input.stock is not None and input.stock < 0:
            errors.append("Stock cannot be negative")
        
        if errors:
            return CreateProduct(
                product=None,
                success=False,
                message="Validation failed",
                errors=errors
            )
        
        try:
            product = Product.objects.create(
                name=input.name,
                price=input.price,
                stock=input.stock if input.stock is not None else 0,
                description=input.description or ""
            )
            
            return CreateProduct(
                product=product,
                success=True,
                message="Product created successfully",
                errors=[]
            )
            
        except Exception as e:
            return CreateProduct(
                product=None,
                success=False,
                message=f"Error creating product: {str(e)}",
                errors=[str(e)]
            )


class CreateOrder(graphene.Mutation):
    """
    Mutation to create an order with products.
    
    Assignment Requirements:
    - Validate customer exists
    - Validate all products exist
    - Calculate total amount from product prices
    - Return order with nested customer and product data
    """
    
    class Arguments:
        input = OrderInput(required=True)
    
    order = Field(OrderType, description="The created order")
    success = Boolean(description="Whether the operation was successful")
    message = String(description="Success or error message")
    errors = List(String, description="List of validation errors")
    
    @staticmethod
    def mutate(root, info, input):
        """Create an order with validation and total calculation"""
        
        errors = []
        
        # Validation 1: Customer must exist
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            errors.append(f"Customer with ID {input.customer_id} does not exist")
        
        # Validation 2: All products must exist
        if not input.product_ids:
            errors.append("At least one product must be specified")
        else:
            existing_products = Product.objects.filter(id__in=input.product_ids)
            if existing_products.count() != len(input.product_ids):
                existing_ids = set(existing_products.values_list('id', flat=True))
                missing_ids = set(input.product_ids) - existing_ids
                errors.append(f"Products with IDs {list(missing_ids)} do not exist")
        
        if errors:
            return CreateOrder(
                order=None,
                success=False,
                message="Validation failed",
                errors=errors
            )
        
        try:
            # Use transaction to ensure data consistency
            with transaction.atomic():
                # Create the order
                order = Order.objects.create(
                    customer=customer,
                    total_amount=0  # We'll calculate this after adding products
                )
                
                # Add products to the order
                products = Product.objects.filter(id__in=input.product_ids)
                order.products.set(products)
                
                # Calculate and save total amount
                total_amount = sum(product.price for product in products)
                order.total_amount = total_amount
                order.save()
                
                return CreateOrder(
                    order=order,
                    success=True,
                    message="Order created successfully",
                    errors=[]
                )
                
        except Exception as e:
            return CreateOrder(
                order=None,
                success=False,
                message=f"Error creating order: {str(e)}",
                errors=[str(e)]
            )


# =============================================
# Queries (for reading data)
# =============================================

class Query(graphene.ObjectType):
    """
    Root Query class that defines all available queries.
    
    This extends the basic "hello" query from Task 0 with full CRM queries.
    """
    
    # Keep the hello query from Task 0
    hello = String(description="Simple greeting to test GraphQL")
    
    # Customer queries
    customer = Field(CustomerType, id=Int(required=True), description="Get a customer by ID")
    all_customers = List(CustomerType, description="Get all customers")
    
    # Product queries
    product = Field(ProductType, id=Int(required=True), description="Get a product by ID")
    all_products = List(ProductType, description="Get all products")
    
    # Order queries
    order = Field(OrderType, id=Int(required=True), description="Get an order by ID")
    all_orders = List(OrderType, description="Get all orders")
    
    # Resolver functions
    def resolve_hello(self, info):
        """Keep the original hello resolver"""
        return "Hello, GraphQL!"
    
    def resolve_customer(self, info, id):
        """Get a single customer by ID"""
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None
    
    def resolve_all_customers(self, info):
        """Get all customers"""
        return Customer.objects.all()
    
    def resolve_product(self, info, id):
        """Get a single product by ID"""
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None
    
    def resolve_all_products(self, info):
        """Get all products"""
        return Product.objects.all()
    
    def resolve_order(self, info, id):
        """Get a single order by ID with related data optimized"""
        try:
            return Order.objects.select_related('customer').prefetch_related('products').get(id=id)
        except Order.DoesNotExist:
            return None
    
    def resolve_all_orders(self, info):
        """Get all orders with optimized queries to prevent N+1 problem"""
        return Order.objects.select_related('customer').prefetch_related('products').all()


# =============================================
# Mutations (combine all mutations)
# =============================================

class Mutation(graphene.ObjectType):
    """
    Root Mutation class that defines all available mutations.
    """
    
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()