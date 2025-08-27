from datetime import datetime
import requests
import json

# from gql.transport.requests import RequestsHTTPTransport", "from gql import", "gql", "Client"]
# /tmp/low_stock_updates_log.txt", "updateLowStockProducts"

def log_crm_heartbeat():
    try:
        timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
        heartbeat_message = f"{timestamp} CRM is alive\n"
        
        with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
            log_file.write(heartbeat_message)
        
        try:
            response = requests.post(
                'http://localhost:8000/graphql',
                json={
                    'query': '{ hello }'
                },
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'data' in result and 'hello' in result['data']:
                    # GraphQL endpoint is responsive
                    with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
                        log_file.write(f"{timestamp} GraphQL endpoint responsive\n")
                else:
                    # GraphQL returned but no hello field
                    with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
                        log_file.write(f"{timestamp} GraphQL endpoint error: No hello field\n")
            else:
                # HTTP error
                with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
                    log_file.write(f"{timestamp} GraphQL endpoint HTTP {response.status_code}\n")
                    
        except requests.exceptions.RequestException as e:
            # Connection failed
            with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
                log_file.write(f"{timestamp} GraphQL endpoint unreachable: {str(e)}\n")
        
        print(f"Heartbeat logged at {timestamp}")
    
    except Exception as e:
        # Log any errors
        timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
        with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
            log_file.write(f"{timestamp} HEARTBEAT ERROR: {str(e)}\n")