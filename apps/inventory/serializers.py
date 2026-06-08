from rest_framework import serializers
from .models import Warehouse, Product, InventoryLevel


class WareHouseSerializer(serializers.ModelSerializer):
    class Meta:
        model=Warehouse
        fields=["id", "name", "code", "address", "is_active", "created_at"]
        read_only_fields=["id", "created_at"]


class InventoryLevelSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)

    class Meta:
        model=InventoryLevel
        fields=["id", "warehouse", "warehouse_name", "warehouse_code", "quantity_on_hand", "reorder_point"]
        read_only_fields=["id"]


class ProductSerializer(serializers.ModelSerializer):
    inventory_balances = InventoryLevelSerializer(many=True, read_only=True)

    class Meta:
        model=Product
        fields=["id", "sku", "description", "wholesale_price", "weight_kg", "inventory_balances", "created_at"]
        read_only_fields=["id", "created_at"]
