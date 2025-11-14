# CRM Celery Report Setup

1. Install Redis and Python dependencies:
   ```bash
   pip install -r requirements.txt
   sudo service redis-server start
Run migrations:

bash
Copy code
python manage.py migrate
Start Celery worker:

bash
Copy code
celery -A crm worker -l info
Start Celery Beat:

bash
Copy code
celery -A crm beat -l info
Verify logs:
Check /tmp/crm_report_log.txt for weekly CRM reports.

yaml
Copy code

---

This setup ensures:

- A **weekly report** is generated every Monday at 6:00 AM.
- It logs **total customers, orders, and revenue**.
- Uses your **GraphQL schema** to fetch the data.
- Celery Beat handles scheduling, and Redis is the broker.