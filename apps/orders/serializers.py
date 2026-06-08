from rest_framework import serializers
from apps.orders.models import Order, OrderItem, Customer

class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()


class OrderCreateSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    items = OrderItemInputSerializer(many=True)


class OrderItemDetailSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_sku', 'product_name', 'quantity', 'unit_price']


class OrderDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
    items = OrderItemDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_id', 'customer_name', 'warehouse_id', 'warehouse_code', 'status', 'total_amount', 'items', 'created_at']