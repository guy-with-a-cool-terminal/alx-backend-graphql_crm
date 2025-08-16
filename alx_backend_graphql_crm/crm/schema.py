import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene import InputObjectType, List, String, Boolean, Field, Int, Decimal, DateTime
from django.core.exceptions import ValidationError
from django.db import transaction
import re
from .models import Customer, Product, Order

# graphql types(converts models to grapghql types)
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"
        description = "A customer in our CRM system"

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"
        description = "A product we sell"

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"
        description = "An order placed by a customer"

# input types for mutations
class CustomerInput(InputObjectType):
    ''' 
    InputObjectType is used when we want to accept complex objects
    as arguments to mutations, rather than individual fields.
    '''
    name = String(required=True,description="Customer's full name")
    email = String(required=True,description="Customer's email address")
    phone = String(description="Customer's phone number")

class ProductInput(InputObjectType):
    name = String(required=True,description="Product name")
    price = Decimal(required=True,description="Product price")
    stock = Int(description="Product stock quantity")
    description = String(description="Product description")

class OrderInput(InputObjectType):
    customer_id = Int(required=True,description="ID of the customer placing the order")
    product_ids = List(Int, required=True,description="List of product IDs in this order")

# mutations for creating and updating data
class CreateCustomer(graphene.Mutation):
    class Arguments:
        # define what args this mutation will accept
        input = CustomerInput(required=True)
        
    # define what this mutation returns
    customer = Field(CustomerType,description="The created customer")
    success = Boolean(description="Whether the operation was successful")
    message = String(description="Success or error message")
    errors = List(String,description="List of validation errors")
    
    @staticmethod
    def mutate(root,info,input):
        '''
        actual function that creates the customer
        '''
        errors = []
        # validation checks
        if Customer.objects.filter(email=input.email).exists():
            errors.append("Email already exists")
        
        if input.phone:
            phone_pattern = r'^(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}$'
            if not re.match(phone_pattern, input.phone):
                errors.append("Invalid phone format. Use +1234567890 or 123-456-7890")
        
        if errors:
            return CreateCustomer(
                customer=None,
                success=False,
                message="Validation failed"
            )
        
        try:
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
    class Arguments:
        input = List(CustomerInput,required=True,description="List of customers to create")
    customers = List(CustomerType, description="Successfully created customers")
    errors = List(String, description="Errors for customers that couldn't be created")
    success_count = Int(description="Number of customers successfully created")
    
    @staticmethod
    def mutate(root,info,input):
        created_customers = []
        errors = []
        
        for i,customer_data in enumerate(input):
            try:
                if Customer.objects.filter(email=customer_data.email).exists():
                    errors.append(f"Customer {i+1}: Email {customer_data.email} already exists")
                    continue

                if customer_data.phone:
                    phone_pattern = r'^(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}$'
                    if not re.match(phone_pattern, customer_data.phone):
                        errors.append(f"Customer {i+1}: Invalid phone format")
                        continue

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

""" Queries ---- reading data """

class Query(graphene.ObjectType):
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
    
    # Filtered queries
    customers = List(
        CustomerType,
        name_icontains=String(description="Filter by name (partial match)"),
        email_icontains=String(description="Filter by email (partial match)"),
        created_at_gte=DateTime(description="Filter by creation date (after)"),
        created_at_lte=DateTime(description="Filter by creation date (before)"),
        phone_pattern=String(description="Filter by phone pattern"),
        description="Get customers with manual filtering"
    )
    
    products = List(
        ProductType,
        name_icontains=String(description="Filter by name"),
        price_gte=Decimal(description="Minimum price"),
        price_lte=Decimal(description="Maximum price"),  
        stock_gte=Int(description="Minimum stock"),
        stock_lte=Int(description="Maximum stock"),
        low_stock=Int(description="Stock below threshold"),
        description="Get products with manual filtering"
    )
    
    orders = List(
        OrderType,
        total_amount_gte=Decimal(description="Minimum total amount"),
        total_amount_lte=Decimal(description="Maximum total amount"),
        order_date_gte=DateTime(description="Orders after date"),
        order_date_lte=DateTime(description="Orders before date"),
        customer_name=String(description="Filter by customer name"),
        product_name=String(description="Filter by product name"),
        description="Get orders with manual filtering"
    )
    
    # Resolver functions
    def resolve_hello(self, info):
        """hello resolver"""
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
    
    def resolve_customers(self, info, **kwargs):
        """Resolve customers with manual filtering"""
        queryset = Customer.objects.all()
        
        name_icontains = kwargs.get('name_icontains')
        if name_icontains:
            queryset = queryset.filter(name__icontains=name_icontains)
        
        email_icontains = kwargs.get('email_icontains')  
        if email_icontains:
            queryset = queryset.filter(email__icontains=email_icontains)
            
        created_at_gte = kwargs.get('created_at_gte')
        if created_at_gte:
            queryset = queryset.filter(created_at__gte=created_at_gte)
            
        created_at_lte = kwargs.get('created_at_lte')
        if created_at_lte:
            queryset = queryset.filter(created_at__lte=created_at_lte)
            
        phone_pattern = kwargs.get('phone_pattern')
        if phone_pattern:
            queryset = queryset.filter(phone__startswith=phone_pattern)
        
        return queryset.order_by('-created_at')
    
    def resolve_products(self, info, **kwargs):
        """Resolve products with manual filtering"""
        queryset = Product.objects.all()
        
        name_icontains = kwargs.get('name_icontains')
        if name_icontains:
            queryset = queryset.filter(name__icontains=name_icontains)
        
        price_gte = kwargs.get('price_gte')
        if price_gte:
            queryset = queryset.filter(price__gte=price_gte)
            
        price_lte = kwargs.get('price_lte')
        if price_lte:
            queryset = queryset.filter(price__lte=price_lte)
            
        stock_gte = kwargs.get('stock_gte')
        if stock_gte:
            queryset = queryset.filter(stock__gte=stock_gte)
            
        stock_lte = kwargs.get('stock_lte')
        if stock_lte:
            queryset = queryset.filter(stock__lte=stock_lte)
            
        low_stock = kwargs.get('low_stock')
        if low_stock:
            queryset = queryset.filter(stock__lt=low_stock)
        
        return queryset.order_by('name')
    
    def resolve_orders(self, info, **kwargs):
        """Resolve orders with manual filtering"""
        queryset = Order.objects.select_related('customer').prefetch_related('products')
        
        total_amount_gte = kwargs.get('total_amount_gte')
        if total_amount_gte:
            queryset = queryset.filter(total_amount__gte=total_amount_gte)
            
        total_amount_lte = kwargs.get('total_amount_lte')
        if total_amount_lte:
            queryset = queryset.filter(total_amount__lte=total_amount_lte)
            
        order_date_gte = kwargs.get('order_date_gte')
        if order_date_gte:
            queryset = queryset.filter(order_date__gte=order_date_gte)
            
        order_date_lte = kwargs.get('order_date_lte')
        if order_date_lte:
            queryset = queryset.filter(order_date__lte=order_date_lte)
            
        customer_name = kwargs.get('customer_name')
        if customer_name:
            queryset = queryset.filter(customer__name__icontains=customer_name)
            
        product_name = kwargs.get('product_name')
        if product_name:
            queryset = queryset.filter(products__name__icontains=product_name).distinct()
        
        return queryset.order_by('-order_date')

# combine all mutations
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()