#!/bin/bash

cd /home/Bri/Desktop/Brian/alx-backend-graphql_crm/alx_backend_graphql
# manage.py
# django management command to delete inactive customers
python3 manage.py shell << EOF
from alx_backend_graphql_crm.crm.models import Customer,Order
from django.utils import timezone
from datetime import timedelta
import sys

cutoff_date = timezone.now() - timedelta(days=365)

inactive_customers = Customer.objects.filter(
    orders__isnull=True
).union(
    Customer.objects.exclude(
        orders__order_date__gte=cutoff_date
    
    )

).distinct()

count = inactive_customers.count()
inactive_customers.delete()

with open('/tmp/customer_cleanup_log.txt','a') as log_file:
    timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    log_file.write(f"{timestamp}: Deleted {count} inactive customers\n")

print(f"Cleanup completed: {count} customers deleted")
EOF