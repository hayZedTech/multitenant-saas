from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.orders.models import Order
from apps.orders.serializers import OrderDetailSerializer, OrderCreateSerializer
from apps.orders.services import OrderPlacementService
from apps.orders.tasks import export_tenant_orders_csv, dispatch_external_webhook
from apps.users.permissions import HasTenantPermission  # 👈 Added our new guard
from django.core.exceptions import ValidationError

class OrderViewSet(viewsets.ModelViewSet):
    """API viewset for reading historical invoices and securely dispatching wholesale B2B orders."""
    queryset = Order.objects.all()
    
    # 🔒 Assign permissions and explicitly map granular permissions to each action
    permission_classes = [HasTenantPermission]
    action_permissions = {
        'list': 'orders:view',
        'retrieve': 'orders:view',
        'create': 'orders:create',
        'trigger_bulk_report_export': 'orders:export_report' # Custom fine-grained power
    }
    
    def get_queryset(self):
        # Enforce strict multi-tenant data isolation at the ORM layer
        return Order.objects.filter(tenant=self.request.user.tenant)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderDetailSerializer

    def create(self, request, *args, **kwargs):
        input_serializer = self.get_serializer_class()(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        validated_data = input_serializer.validated_data

        try:
            # 1. Execute safe high-concurrency database row-lock transaction
            new_order = OrderPlacementService.create_b2b_order(
                customer_id=validated_data['customer_id'],
                warehouse_id=validated_data['warehouse_id'],
                order_items_data=validated_data['items']
            )
            
            # 2. 🔥 FIRE AND FORGET WEBHOOK: Offload downstream network operations to Celery
            mock_tenant_webhook_url = "https://tenant-external-erp-system.com/webhooks/orders"
            
            dispatch_external_webhook.delay(
                target_url=mock_tenant_webhook_url,
                event_type="ORDER.PROCESSED_SUCCESSFULLY",
                payload={"order_id": new_order.id, "total_invoice_value": float(new_order.total_amount)}
            )
            
            output_serializer = OrderDetailSerializer(new_order)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as error:
            return Response({"error": str(error.message)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='export-report')
    def trigger_bulk_report_export(self, request):
        """Triggers an out-of-band asynchronous processing job to compile tenant historical data logs."""
        target_email = request.data.get("email")
        if not target_email:
            return Response({"error": "The destination 'email' property is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Extract active tenant metadata from request context layer
        active_tenant = request.user.tenant
        
        # Dispatch task down onto Celery Redis Queue
        export_tenant_orders_csv.delay(tenant_id=active_tenant.id, target_email=target_email)
        
        return Response({
            "status": "Asynchronous compilation job successfully initialized.",
            "message": f"A secure download link will be dispatched to {target_email} upon completion."
        }, status=status.HTTP_202_ACCEPTED)