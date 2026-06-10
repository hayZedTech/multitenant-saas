from django.db import models
from apps.tenants.models import Tenant

class Permission(models.Model):
    """
    Global system-wide granular permissions.
    Examples: 'orders:view', 'orders:create', 'orders:export_report'
    """
    name = models.CharField(max_length=100)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Role(models.Model):
    """
    Tenant-isolated roles that aggregate multiple system permissions.
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="roles")
    name = models.CharField(max_length=50)
    permissions = models.ManyToManyField(Permission, related_name="roles", blank=True)
    is_system_role = models.BooleanField(default=False)

    class Meta:
        unique_together = ('tenant', 'name')

    def __str__(self):
        return f"{self.tenant.name} - {self.name}"