import django_filters
from django_filters import FilterSet, CharFilter, DateFilter, DecimalFilter, NumberFilter, ModelMultipleChoiceFilter, MethodFilter
from django.db.models import Q

from .models import Customer, Product, Order

class CustomerFilter(FilterSet):
    """
    Filter set for the Customer model, enabling searches by name, email, and creation date range.
    """
    # Case-insensitive partial match
    name = CharFilter(field_name='name', lookup_expr='icontains')
    email = CharFilter(field_name='email', lookup_expr='icontains')

    # Date range filters (e.g., createdAtGte, createdAtLte)
    created_at__gte = DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_at__lte = DateFilter(field_name='created_at', lookup_expr='date__lte')

    # Challenge: Custom filter to match phone number patterns (starts with +1)
    # The filter name in GraphQL will be 'phonePattern' based on the method name
    phone_pattern = MethodFilter(method='filter_by_phone_pattern')

    class Meta:
        model = Customer
        # Define fields that can be filtered with standard lookups (optional, often better to define explicitly)
        fields = ['name', 'email', 'created_at']

    def filter_by_phone_pattern(self, queryset, name, value):
        """Filters customers where the phone number starts with the given value (e.g., '+1')."""
        if value:
            # Filters where the phone field starts with the given value (case-sensitive as phone is usually exact)
            return queryset.filter(phone__startswith=value)
        return queryset


class ProductFilter(FilterSet):
    """
    Filter set for the Product model, enabling searches by name, price range, and stock range.
    """
    name = CharFilter(field_name='name', lookup_expr='icontains')

    # Price range filters (e.g., priceGte, priceLte)
    price__gte = DecimalFilter(field_name='price', lookup_expr='gte')
    price__lte = DecimalFilter(field_name='price', lookup_expr='lte')

    # Stock range filters (e.g., stockGte, stockLte)
    stock__gte = NumberFilter(field_name='stock', lookup_expr='gte')
    stock__lte = NumberFilter(field_name='stock', lookup_expr='lte')

    # Challenge: Filter products with low stock (e.g., stock < 10)
    low_stock = MethodFilter(method='filter_low_stock')

    class Meta:
        model = Product
        fields = ['name', 'price', 'stock']

    def filter_low_stock(self, queryset, name, value):
        """If true, filters products where stock is less than 10."""
        if value: # Assuming value is a boolean (or truthy/falsy equivalent)
            return queryset.filter(stock__lt=10)
        return queryset


class OrderFilter(FilterSet):
    """
    Filter set for the Order model, including filters on related Customer and Product models.
    """
    # Total amount range
    total_amount__gte = DecimalFilter(field_name='total_amount', lookup_expr='gte')
    total_amount__lte = DecimalFilter(field_name='total_amount', lookup_expr='lte')

    # Order date range
    order_date__gte = DateFilter(field_name='order_date', lookup_expr='date__gte')
    order_date__lte = DateFilter(field_name='order_date', lookup_expr='date__lte')

    # Filter by related customer's name (case-insensitive partial match)
    customer_name = CharFilter(field_name='customer__name', lookup_expr='icontains', distinct=True)

    # Filter by associated product's name (case-insensitive partial match)
    product_name = CharFilter(field_name='products__name', lookup_expr='icontains', distinct=True)

    # Challenge: Allow filtering orders that include a specific product ID.
    # We use a CharFilter with a 'products__id' lookup, expecting a UUID/ID string.
    product_id = CharFilter(field_name='products__id', lookup_expr='exact', distinct=True)


    class Meta:
        model = Order
        fields = ['total_amount', 'order_date', 'customer_name', 'product_name']
