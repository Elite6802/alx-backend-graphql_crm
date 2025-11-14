# CRM Project Setup

This project includes several scheduled tasks and reports for CRM management:

- Heartbeat logger
- Order reminders
- Low-stock product updates
- Weekly CRM report via Celery

---

## 1. Install Dependencies

Install Python packages:

```bash
pip install -r requirements.txt
pip install celery django-celery-beat gql django-crontab
Install and start Redis:

bash
sudo apt install redis-server   # For Linux
sudo service redis-server start
2. Django Migrations
Run migrations to set up the database:

bash
python manage.py migrate
3. Cron Jobs Setup
Heartbeat Logger
Logs every 5 minutes to /tmp/crm_heartbeat_log.txt:

python
# crm/cron.py
from datetime import datetime

def log_crm_heartbeat():
    log_file = "/tmp/crm_heartbeat_log.txt"
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"{timestamp} CRM is alive\n")
Add to crm/settings.py:

python
INSTALLED_APPS += ["django_crontab"]

CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
]
Order Reminders
Sends reminders for orders placed in the last 7 days.

Logs to /tmp/order_reminders_log.txt.

Cron schedule in crm/cron_jobs/order_reminders_crontab.txt:

text
0 8 * * * /usr/bin/python3 /path/to/alx-backend-graphql_crm/crm/cron_jobs/send_order_reminders.py
Low-Stock Product Updates
Runs every 12 hours.

Increments stock by 10 for products with stock < 10.

Logs to /tmp/low_stock_updates_log.txt.

Cron schedule in crm/settings.py:

python
CRONJOBS += [
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]
4. Celery Setup for Weekly CRM Reports
Celery Configuration
Add to crm/settings.py:

python
INSTALLED_APPS += ["django_celery_beat"]

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}
Celery Initialization
crm/celery.py:

python
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')

app = Celery('crm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
crm/__init__.py:

python

from .celery import app as celery_app
__all__ = ['celery_app']
CRM Report Task
crm/tasks.py:

python

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
5. Running the Project
Start the Django server:

bash
python manage.py runserver
Start Celery worker:

celery -A crm worker -l info
Start Celery Beat:

celery -A crm beat -l info
Verify Logs:

Heartbeat: /tmp/crm_heartbeat_log.txt

Order reminders: /tmp/order_reminders_log.txt

Low-stock updates: /tmp/low_stock_updates_log.txt

Weekly report: /tmp/crm_report_log.txt