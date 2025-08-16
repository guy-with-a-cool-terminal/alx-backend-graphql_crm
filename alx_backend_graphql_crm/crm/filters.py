import django_filters
from django_filters import FilterSet, CharFilter, NumberFilter, DateTimeFilter
from .models import Customer, Product, Order

class CustomerFilter(FilterSet):
    """
    Filter class for Customer queries.
    
    Allows filtering customers by:
    - name: Case-insensitive partial match
    - email: Case-insensitive partial match  
    - created_at: Date range filtering
    - phone_pattern: Custom filter for phone numbers starting with specific pattern
    """
    # case-insensitive search
    name = CharFilter(
        field_name='name',
        lookup_expr='icontains',
        help_text="Filter by customer name (partial match, case-insensitive)"
    )
    
    email = CharFilter(
        field_name='email', 
        lookup_expr='icontains',
        help_text="Filter by email address (partial match, case-insensitive)"
    )
    
    # Date range filters for creation date
    created_at_gte = DateTimeFilter(
        field_name='created_at', 
        lookup_expr='gte',  # Greater than or equal
        help_text="Filter customers created after this date/time"
    )
    
    created_at_lte = DateTimeFilter(
        field_name='created_at', 
        lookup_expr='lte',  # Less than or equal
        help_text="Filter customers created before this date/time"
    )
    
    # Custom filter for phone number patterns
    phone_pattern = CharFilter(
        field_name='phone', 
        lookup_expr='startswith',
        help_text="Filter by phone numbers starting with pattern (e.g., '+1' for US numbers)"
    )
    
    class Meta:
        model = Customer
        fields = []
class ProductFilter(FilterSet):
    """
    Filter class for Product queries.
    
    Allows filtering products by:
    - name: Case-insensitive partial match
    - price: Range filtering (min/max price)
    - stock: Range filtering (min/max stock)
    - low_stock: Custom filter for products with stock below threshold
    """
    
    # Case-insensitive partial name search
    name = CharFilter(
        field_name='name', 
        lookup_expr='icontains',
        help_text="Filter by product name (partial match, case-insensitive)"
    )
    
    # Price range filters
    price_gte = NumberFilter(
        field_name='price', 
        lookup_expr='gte',
        help_text="Filter products with price greater than or equal to this value"
    )
    
    price_lte = NumberFilter(
        field_name='price', 
        lookup_expr='lte',
        help_text="Filter products with price less than or equal to this value"
    )
    
    # Stock range filters
    stock_gte = NumberFilter(
        field_name='stock', 
        lookup_expr='gte',
        help_text="Filter products with stock greater than or equal to this value"
    )
    
    stock_lte = NumberFilter(
        field_name='stock', 
        lookup_expr='lte',
        help_text="Filter products with stock less than or equal to this value"
    )
    
    # Custom filter for low stock products
    low_stock = NumberFilter(
        field_name='stock', 
        lookup_expr='lt',  # Less than
        help_text="Filter products with stock below this threshold (e.g., 10 for low stock)"
    )
    
    class Meta:
        model = Product
        fields = []


class OrderFilter(FilterSet):
    """
    Filter class for Order queries.
    
    Allows filtering orders by:
    - total_amount: Range filtering
    - order_date: Date range filtering
    - customer_name: Filter by customer's name (using related field)
    - product_name: Filter by product name (using many-to-many relation)
    - customer_email: Additional filter by customer email
    """
    
    # Total amount range filters
    total_amount_gte = NumberFilter(
        field_name='total_amount', 
        lookup_expr='gte',
        help_text="Filter orders with total amount greater than or equal to this value"
    )
    
    total_amount_lte = NumberFilter(
        field_name='total_amount', 
        lookup_expr='lte',
        help_text="Filter orders with total amount less than or equal to this value"
    )
    
    # Order date range filters
    order_date_gte = DateTimeFilter(
        field_name='order_date', 
        lookup_expr='gte',
        help_text="Filter orders placed after this date/time"
    )
    
    order_date_lte = DateTimeFilter(
        field_name='order_date', 
        lookup_expr='lte',
        help_text="Filter orders placed before this date/time"
    )
    
    # Filter by customer name (using related field lookup)
    customer_name = CharFilter(
        field_name='customer__name',  # Double underscore for related field
        lookup_expr='icontains',
        help_text="Filter orders by customer name (partial match, case-insensitive)"
    )
    
    # Filter by customer email (additional useful filter)
    customer_email = CharFilter(
        field_name='customer__email',
        lookup_expr='icontains',
        help_text="Filter orders by customer email (partial match, case-insensitive)"
    )
    
    # Filter by product name (using many-to-many relation)
    product_name = CharFilter(
        field_name='products__name',  # Many-to-many relation
        lookup_expr='icontains',
        help_text="Filter orders containing products with this name"
    )
    
    # Custom filter: orders that include a specific product ID
    product_id = NumberFilter(
        field_name='products__id',
        lookup_expr='exact',
        help_text="Filter orders that include the product with this ID"
    )
    
    class Meta:
        model = Order
        fields = []


# Additional utility functions for complex filtering

def get_customers_by_order_count(min_orders=1):
    """
    Utility function to get customers who have placed at least X orders.
    This can be used in custom resolvers for advanced filtering.
    """
    from django.db.models import Count
    return Customer.objects.annotate(
        order_count=Count('orders')
    ).filter(order_count__gte=min_orders)


def get_products_by_popularity(min_orders=1):
    """
    Utility function to get products that appear in at least X orders.
    Useful for finding popular products.
    """
    from django.db.models import Count
    return Product.objects.annotate(
        order_count=Count('orders')
    ).filter(order_count__gte=min_orders)


def get_high_value_orders(min_amount=1000):
    """
    Utility function to get high-value orders above a threshold.
    """
    return Order.objects.filter(total_amount__gte=min_amount)