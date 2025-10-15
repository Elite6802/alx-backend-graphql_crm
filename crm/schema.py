import graphene
from graphene_django.types import DjangoObjectType
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal, InvalidOperation
import re
import json # Used to format structured error output

from .models import Customer, Product, Order

# --- 1. Graphene Types (Outputs) ---

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ('id', 'name', 'email', 'phone', 'created_at')

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock', 'created_at')

class OrderType(DjangoObjectType):
    # Ensure nested products are returned as a list of ProductType
    products = graphene.List(ProductType)

    class Meta:
        model = Order
        fields = ('id', 'customer', 'products', 'total_amount', 'order_date')


# --- 2. Graphene Inputs (Used for Arguments in Mutations) ---

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False)

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    # Use List of IDs to handle multiple products
    product_ids = graphene.List(graphene.ID, required=True)


# --- 3. Validation Helpers ---

def validate_phone_format(phone):
    """
    Validates phone format (e.g., +1234567890 or 123-456-7890).
    """
    if phone:
        # Simple regex allowing digits, spaces, hyphens, and leading +
        if not re.match(r'^\+?[\d\s-]{7,20}$', str(phone)):
            raise ValidationError("Invalid phone format. Please use digits, hyphens, or include country code with '+'.")

def validate_customer_data(data):
    """
    Performs all customer-specific validations.
    Returns None on success, or a detailed error message string on failure.
    """
    if Customer.objects.filter(email=data.email).exists():
        return f"Email '{data.email}' already exists."

    try:
        validate_email(data.email)
    except ValidationError:
        return f"Email '{data.email}' is not a valid email address."

    try:
        if data.phone:
            validate_phone_format(data.phone)
    except ValidationError as e:
        # Convert error to string format
        return f"Phone validation failed for '{data.phone}': {e.message}"

    return None

# --- 4. Mutation Classes ---

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    # Output fields
    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input=None):
        error_message = validate_customer_data(input)
        if error_message:
            # Raising an exception handles the error robustly within Graphene
            raise Exception(error_message)

        customer = Customer.objects.create(
            name=input.name,
            email=input.email,
            phone=input.phone
        )
        return CreateCustomer(customer=customer, message="Customer created successfully.")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        # Accepts a list of CustomerInput objects
        input = graphene.List(CustomerInput, required=True)

    # Output fields
    customers = graphene.List(CustomerType)
    # Errors are returned as a list of strings (JSON formatted for structure)
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, input=None):
        created_customers = []
        errors = []

        # Challenge: Support partial success
        for i, customer_data in enumerate(input):
            try:
                # 1. Validation
                error_message = validate_customer_data(customer_data)

                if error_message:
                    # Collect error and continue to next customer
                    errors.append(json.dumps({
                        'index': i,
                        'email': customer_data.email,
                        'error': error_message
                    }))
                    continue

                # 2. Creation
                customer = Customer.objects.create(
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.phone
                )
                created_customers.append(customer)

            except Exception as e:
                # Catch any unexpected system errors (e.g., database connection failure)
                errors.append(json.dumps({
                    'index': i,
                    'email': customer_data.email,
                    'error': f"Internal error: {str(e)}"
                }))

        return BulkCreateCustomers(customers=created_customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    @staticmethod
    def mutate(root, info, input=None):
        # Validation
        if input.price <= Decimal('0'):
            raise Exception("Price must be a positive number.")
        if input.stock is not None and input.stock < 0:
            raise Exception("Stock cannot be a negative number.")

        try:
            # stock defaults to 0 if not provided
            stock_value = input.stock if input.stock is not None else 0

            product = Product.objects.create(
                name=input.name,
                price=input.price,
                stock=stock_value
            )
            return CreateProduct(product=product)
        except InvalidOperation:
            raise Exception("Invalid price format provided. Ensure it is a valid decimal number.")


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    @staticmethod
    @transaction.atomic # Ensure all database operations are completed successfully or rolled back
    def mutate(root, info, input=None):
        customer_id = input.customer_id
        product_ids = input.product_ids

        # Validation 1: Product list not empty
        if not product_ids:
            raise Exception("Order must include at least one product ID.")

        # Validation 2: Customer existence
        try:
            customer = Customer.objects.get(id=customer_id)
        except (Customer.DoesNotExist, ValidationError):
             # ValidationError catches invalid UUID format
            raise Exception(f"Invalid customer ID: '{customer_id}' was not found.")

        # Validation 3: Product existence and fetching
        # Use a list of unique IDs to prevent duplicate products causing issues
        unique_product_ids = list(set(product_ids))
        products = Product.objects.filter(id__in=unique_product_ids)

        if products.count() != len(unique_product_ids):
            existing_ids = set(str(p.id) for p in products)
            all_ids = set(unique_product_ids)
            invalid_ids = list(all_ids - existing_ids)
            raise Exception(f"One or more product IDs are invalid: {', '.join(invalid_ids)}")

        # 4. Calculate total amount
        total_amount = sum(p.price for p in products)

        # 5. Create the Order object
        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount
        )

        # 6. Associate products
        order.products.set(products)

        return CreateOrder(order=order)


# --- 5. CRM App Root Query and Mutation ---

class CRMQuery(graphene.ObjectType):
    """
    Root query fields for the crm app.
    We add a simple query to retrieve customers for testing the mutation output.
    """
    customer = graphene.Field(CustomerType, id=graphene.ID())
    all_customers = graphene.List(CustomerType)

    def resolve_customer(root, info, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None

    def resolve_all_customers(root, info):
        # Sort for predictable results
        return Customer.objects.all().order_by('name')

class CRMMutation(graphene.ObjectType):
    """
    Aggregates all the individual mutation classes.
    """
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
