import graphene
from graphene import Field, List
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import Customer, Product, Order
from django.utils import timezone


# -----------------------------
# GraphQL Types
# -----------------------------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")


# -----------------------------
# CreateCustomer Mutation
# -----------------------------
class CreateCustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CreateCustomerInput(required=True)

    customer = Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        name = input.name
        email = input.email
        phone = input.phone

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            raise Exception("Invalid email format.")

        # Ensure email is unique
        if Customer.objects.filter(email=email).exists():
            raise Exception("Email already exists.")

        # Optional: Validate phone format
        if phone and not phone.replace("+", "").replace("-", "").isdigit():
            raise Exception("Invalid phone format. Use +1234567890 or 123-456-7890.")

        customer = Customer.objects.create(name=name, email=email, phone=phone)

        return CreateCustomer(customer=customer, message="Customer created successfully.")


# -----------------------------
# BulkCreateCustomers Mutation
# -----------------------------
class BulkCustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = List(BulkCustomerInput, required=True)

    customers = List(CustomerType)
    errors = List(graphene.String)

    def mutate(self, info, input):
        created = []
        errors = []

        for index, entry in enumerate(input):
            try:
                validate_email(entry.email)

                if Customer.objects.filter(email=entry.email).exists():
                    raise Exception(f"Duplicate email: {entry.email}")

                customer = Customer(
                    name=entry.name,
                    email=entry.email,
                    phone=entry.phone
                )
                customer.save()
                created.append(customer)

            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")

        return BulkCreateCustomers(customers=created, errors=errors)


# -----------------------------
# CreateProduct Mutation
# -----------------------------
class CreateProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int(required=False, default_value=0)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = CreateProductInput(required=True)

    product = Field(ProductType)

    def mutate(self, info, input):
        if input.price <= 0:
            raise Exception("Price must be positive.")

        if input.stock < 0:
            raise Exception("Stock cannot be negative.")

        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock
        )

        return CreateProduct(product=product)


# -----------------------------
# CreateOrder Mutation
# -----------------------------
class CreateOrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = CreateOrderInput(required=True)

    order = Field(OrderType)

    def mutate(self, info, input):
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID.")

        if not input.product_ids:
            raise Exception("At least one product must be selected.")

        products = []
        total = 0

        for pid in input.product_ids:
            try:
                product = Product.objects.get(id=pid)
                products.append(product)
                total += float(product.price)
            except Product.DoesNotExist:
                raise Exception(f"Invalid product ID: {pid}")

        order = Order.objects.create(
            customer=customer,
            order_date=input.order_date or timezone.now(),
            total_amount=total
        )

        order.products.set(products)

        return CreateOrder(order=order)


# -----------------------------
# Schema Combination
# -----------------------------
class Query(graphene.ObjectType):
    customers = List(CustomerType)
    products = List(ProductType)
    orders = List(OrderType)

    def resolve_customers(root, info):
        return Customer.objects.all()

    def resolve_products(root, info):
        return Product.objects.all()

    def resolve_orders(root, info):
        return Order.objects.all()


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
