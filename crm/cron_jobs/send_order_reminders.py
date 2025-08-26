#!/usr/bin/env python3
import os
import sys
import django
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

sys.path.append('/home/Bri/Desktop/Brian/alx-backend-graphql_crm/alx_backend_graphql')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

def send_order_reminders():
    try:
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            use_json=True,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # claculate the date
        seven_days_ago = datetime.now() - timedelta(days=7)
        date_filter = seven_days_ago.strftime('%Y-%m-%d')
        
        # GraphQL query to find recent pending orders
        query = gql("""
            query GetRecentOrders($dateFilter: String!) {
                orders(orderDate_Gte: $dateFilter) {
                    edges {
                        node {
                            id
                            orderDate
                            status
                            customer {
                                email
                                firstName
                                lastName
                            }
                        }
                    }
                }
            }
        """)
        
        # execute query
        variables = {"dateFilter": date_filter}
        result = client.execute(query,variable_values=variables)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open('/tmp/order_reminders_log.txt', 'a') as log_file:
            log_file.write(f"{timestamp}: Processing order reminders\n")
            
            orders = result.get('orders', {}).get('edges', [])
            
            for order_edge in orders:
                order = order_edge['node']
                order_id = order['id']
                customer_email = order['customer']['email']
                customer_name = f"{order['customer']['firstName']} {order['customer']['lastName']}"
                order_date = order['orderDate']
                
                log_entry = f"{timestamp}: Order ID {order_id} - Customer: {customer_email} ({customer_name}) - Order Date: {order_date}\n"
                log_file.write(log_entry)
            
            if not orders:
                log_file.write(f"{timestamp}: No recent orders found\n")
        
        print("Order reminders processed!")
        
    except Exception as e:
        # Log errors
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('/tmp/order_reminders_log.txt', 'a') as log_file:
            log_file.write(f"{timestamp}: ERROR - {str(e)}\n")
        print(f"Error processing reminders: {e}")

if __name__ == "__main__":
    send_order_reminders()