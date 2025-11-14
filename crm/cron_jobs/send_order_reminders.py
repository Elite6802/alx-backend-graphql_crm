#!/usr/bin/env python3
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import datetime
import os

# -----------------------------
# Logging setup
# -----------------------------
log_file = "crm/cron_jobs/logs/order_reminders_log.txt"
os.makedirs(os.path.dirname(log_file), exist_ok=True)

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
# Query orders
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

# Get datetime for 7 days ago
seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()

try:
    result = client.execute(query)
    orders = result.get("orders", [])

    # Filter orders from the last 7 days
    recent_orders = [o for o in orders if o["orderDate"] >= seven_days_ago]

    # Log to file
    with open(log_file, "a") as f:
        for order in recent_orders:
            f.write(f"{datetime.datetime.now()} - Order ID {order['id']}, Customer {order['customer']['email']}\n")

    print("Order reminders processed!")

except Exception as e:
    print("Error fetching orders:", e)
