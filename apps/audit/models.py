from django.db import models
from apps.tenants.models import TenantModel
# Pointing strictly to your single master user model location
from django.conf import settings 

class AuditLog(TenantModel):
    """
    Tracks critical system mutations cleanly scoped under specific tenant domains.
    """
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="audit_actions"
    )
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES)
    module_name = models.CharField(max_length=100)  # e.g., 'orders', 'inventory', 'customers'
    record_id = models.PositiveIntegerField()       # ID of the mutated record
    payload_before = models.JSONField(blank=True, null=True) # State prior to change
    payload_after = models.JSONField(blank=True, null=True)  # State after change
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.module_name.upper()} | {self.action_type} by {self.actor} at {self.created_at}"