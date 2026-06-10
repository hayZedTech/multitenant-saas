from rest_framework import viewsets
from apps.orders.models import Customer  # 👈 Pointing to the true master model
from apps.customers.serializers import CustomerSerializer
from apps.users.permissions import HasTenantPermission

class CustomerViewSet(viewsets.ModelViewSet):
    """
    API viewset for managing tenant customer records.
    Fully isolated via your TenantModel core hooks and restricted by RBAC guards.
    """
    serializer_class = CustomerSerializer
    permission_classes = [HasTenantPermission]
    
    # Action-based permissions mapping for our seeded security tokens
    action_permissions = {
        'list': 'customers:view',
        'retrieve': 'customers:view',
        'create': 'customers:manage',
        'update': 'customers:manage',
        'partial_update': 'customers:manage',
        'destroy': 'customers:manage'
    }

    def get_queryset(self):
        # Fallback to your custom TenantManager thread-local context isolation implicitly
        return Customer.objects.filter(is_active=True)