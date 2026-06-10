from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.tenants.models import Tenant
from apps.users.models import Role, Permission

@receiver(post_save, sender=Tenant)
def provision_default_tenant_roles(sender, instance, created, **kwargs):
    """
    Automatically initializes tenant-scoped roles using your clean architecture.
    """
    if not created:
        return

    all_permissions = {perm.codename: perm for perm in Permission.objects.all()}
    
    role_templates = {
        "Owner": ["orders:view", "orders:create", "orders:export_report", "customers:view", "customers:manage"],
        "Manager": ["orders:view", "orders:create", "customers:view", "customers:manage"],
        "Cashier": ["orders:view", "orders:create", "customers:view"]
    }

    for role_name, allowed_codenames in role_templates.items():
        role, _ = Role.objects.get_or_create(
            tenant=instance,
            name=role_name,
            defaults={"is_system_role": True}
        )
        matched_perms = [all_permissions[code] for code in allowed_codenames if code in all_permissions]
        role.permissions.set(matched_perms)