from rest_framework.permissions import BasePermission
from apps.tenants.utils import get_current_tenant

class HasTenantPermission(BasePermission):
    """
    Strictly validates roles and permissions within the current active tenant context.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Use your thread-local utility to get context
        current_tenant = get_current_tenant()
        if not current_tenant or request.user.tenant != current_tenant:
            return False

        # Bypass checks entirely if the user is designated as the root Tenant Admin
        if request.user.is_tenant_admin:
            return True

        # Resolve action string mappings from the view configuration
        action_permission_map = getattr(view, 'action_permissions', {})
        required_permission = action_permission_map.get(view.action)

        if not required_permission:
            return False

        # Validate against the user's explicit tenant role assignments
        if not request.user.role:
            return False

        return request.user.role.permissions.filter(codename=required_permission).exists()