from rest_framework import serializers
from apps.orders.models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    """
    Handles serialization for customer profiles.
    Fully maps to the extended orders.Customer database columns.
    """
    
    class Meta:
        model = Customer
        fields = [
            'id', 
            'company_name', 
            'contact_name',
            'email', 
            'phone_number',
            'shipping_address',
            'tier_discount_percentage',
            'created_at', 
            'updated_at'
        ]
        # Protect structural fields from being modified manually via API requests
        read_only_fields = ['id', 'created_at', 'updated_at']