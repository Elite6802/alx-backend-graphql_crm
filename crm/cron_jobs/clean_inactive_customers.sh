#!/bin/bash
# Script to delete inactive customers and log result

# Run Django shell command
deleted_count=$(python C:/Users/hp/Desktop/ASSIGNMENTS/alx-backend-graphql_crm/manage.py shell -c "
from crm.models import Customer
from django.utils import timezone
from datetime import timedelta

one_year_ago = timezone.now() - timedelta(days=365)

# Adjust according to your order model
qs = Customer.objects.filter(orders__isnull=True)
count = qs.count()
qs.delete()
print(count)
")

# Log result with timestamp
echo "$(date '+%Y-%m-%d %H:%M:%S') - Deleted $deleted_count inactive customers" >> C:/Users/hp/Desktop/ASSIGNMENTS/alx-backend-graphql_crm/crm/cron_jobs/customer_cleanup_log.txt
