import os
import datetime
import requests
from gql.transport.requests import RequestsHTTPTransport
from gql import gql, Client

# Path for log file (Windows/Unix safe)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(BASE_DIR, "logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "/tmp/crm_heartbeat_log.txt")


def log_crm_heartbeat():
    """Logs heartbeat messages to confirm CRM is alive."""
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{timestamp} CRM is alive\n"

    # Append message to log file
    with open(log_file, "a") as f:
        f.write(message)

    # Optionally, ping the GraphQL endpoint
    try:
        response = requests.post(
            "http://127.0.0.1:8000/graphql",
            json={"query": "{ hello }"},
            timeout=5
        )
        if response.status_code == 200:
            with open(log_file, "a") as f:
                f.write(f"{timestamp} GraphQL endpoint responsive\n")
        else:
            with open(log_file, "a") as f:
                f.write(f"{timestamp} GraphQL endpoint returned status {response.status_code}\n")
    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"{timestamp} Error pinging GraphQL endpoint: {e}\n")
