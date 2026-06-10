from rest_framework import serializers
from apps.audit.models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'actor_username',
            'action_type',
            'module_name',
            'record_id',
            'payload_before',
            'payload_after',
            'ip_address',
            'created_at'
        ]
        read_only_fields = fields