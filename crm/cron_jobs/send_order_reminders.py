#!/usr/bin/env python3
import os
import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# -----------------------------
# Logging setup (Windows + Unix safe)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(BASE_DIR, "logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "order_reminders_crontab.txt")

# -----------------------------
# GraphQL Client setup
# -----------------------------
transport = RequestsHTTPTransport(
    url="http://127.0.0.1:8000/graphql",
    verify=False,
    retries=3,
)
client = Client(transport=transport, fetch_schema_from_transport=True)

# -----------------------------
# GraphQL Query
# -----------------------------
query = gql("""
query {
  orders {
    id
    orderDate
    customer {
      email
    }
  }
}
""")

seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()

try:
    result = client.execute(query)
    orders = result.get("orders", [])

    # Filter orders from the last 7 days
    recent_orders = [o for o in orders if o["orderDate"] >= seven_days_ago]

    with open(log_file, "a") as f:
        for order in recent_orders:
            f.write(f"{datetime.datetime.now()} - Order ID {order['id']}, Customer {order['customer']['email']}\n")

    print("Order reminders processed!")

except Exception as e:
    print("Error fetching orders:", e)
