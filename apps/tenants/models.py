from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.tenants.utils import get_current_tenant
from django.core.exceptions import ValidationError

class Tenant(models.Model):
    name=models.CharField(max_length=255)
    owner_domain=models.CharField(max_length=255)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class User(AbstractUser):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="users", blank=True, null=True)
    is_tenant_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} {self.tenant.name if self.tenant else "Global Admin"}"
    

class TenantQuerySet(models.QuerySet):
    def filter(self, *args, **kwargs):
        current_tenant = get_current_tenant()
        if current_tenant:
            kwargs["tenant"] = current_tenant
        return super().save(*args, **kwargs)
    

class TenantManager(models.Manager):
    def get_queryset(self):
        current_tenant=get_current_tenant()
        base_queryset = TenantQuerySet(self.model, using=self._db)
        if current_tenant:
            return base_queryset(tenant=current_tenant)
        return base_queryset


class TenantModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="%(class)s_records")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    objects = TenantManager()
    un_scoped_objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        current_tenant = get_current_tenant()
        if current_tenant:
            self.tenant = current_tenant
        elif not self.tenant_id:
            raise ValidationError("An active tenant is needed")
        return super().save(*args, **kwargs)
