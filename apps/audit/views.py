from rest_framework import viewsets, mixins
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.users.permissions import HasTenantPermission

class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint to securely query immutable historical mutation logs.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [HasTenantPermission]
    
    # Restrict endpoint using our seeded token map
    action_permissions = {
        'list': 'audit:view',
        'retrieve': 'audit:view'
    }

    def get_queryset(self):
        # Implicitly scopes data strictly within the thread-local tenant workspace boundary
        return AuditLog.objects.all()