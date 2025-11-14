# crm/tasks.py
from celery import shared_task
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

@shared_task
def generate_crm_report():
    log_file = "/tmp/crm_report_log.txt"
    transport = RequestsHTTPTransport(
        url="http://127.0.0.1:8000/graphql",
        verify=False,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    query = gql(
        """
        query {
            allCustomers { totalCount }
            allOrders { totalCount, totalAmountSum }
        }
        """
    )

    try:
        result = client.execute(query)
        total_customers = result['allCustomers']['totalCount']
        total_orders = result['allOrders']['totalCount']
        total_revenue = result['allOrders']['totalAmountSum']

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as f:
            f.write(f"{timestamp} - Report: {total_customers} customers, {total_orders} orders, {total_revenue} revenue\n")
    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error generating report: {str(e)}\n")
