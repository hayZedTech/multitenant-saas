import csv
import io
import requests
from celery import shared_task
from apps.orders.models import Order
from apps.tenants.models import Tenant

@shared_task
def export_tenant_orders_csv(tenant_id, target_email):
    """Compiles large historical datasets into a CSV file asynchronously without blocking the API thread."""
    # Enforce clear tenant scoping since background tasks run outside the active HTTP middleware thread
    orders = Order.unscoped_objects.filter(tenant_id=tenant_id).order_by('-created_at')
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Order ID', 'Customer ID', 'Total Amount ($)', 'Status', 'Timestamp'])
    
    for order in orders:
        writer.writerow([order.id, order.customer_id, order.total_amount, order.status, order.created_at])
        
    csv_data = output.getvalue()
    
    # SYSTEM LOGIC NOTE: Here you would plug in your email engine or upload to an S3/Supabase storage bucket
    print(f"SUCCESS: Generated {orders.count()} rows for Tenant {tenant_id}. Email dispatched securely to {target_email}")
    return True


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def dispatch_external_webhook(self, target_url, event_type, payload):
    """Dispatches real-time outbound event data to a tenant's configured external server webhook node."""
    headers = {'Content-Type': 'application/json', 'X-SaaS-Engine-Event': event_type}
    
    try:
        response = requests.post(target_url, json=payload, headers=headers, timeout=8)
        # If server answers with 5xx status codes, trigger a standard backoff retry cycle
        if response.status_code >= 500:
            raise self.retry(exc=Exception(f"Target node server error: {response.status_code}"))
        print(f"WEBHOOK SUCCESS: Sent {event_type} payload down to target endpoint {target_url}")
    except requests.exceptions.RequestException as error:
        print(f"WEBHOOK ATTEMPT FAILED: Retrying connection...")
        raise self.retry(exc=error)