from .models import Warehouse, Product, InventoryLevel
from .serializers import WareHouseSerializer, InventoryLevelSerializer, ProductSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WareHouseSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


    @action(methods=["post"], detail=True, url_path="adjust_stock")
    def adjust_stock(self, request, pk=None):
        product = self.get_object()
        warehouse_id = request.data.get("warehouse_id")
        adjustment = request.data.get("adjustment")

        if not warehouse_id or adjustment is None:
            return Response({"error":"Both warehouse_id and adjustment are reqiured!"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            warehouse = Warehouse.objects.get(pk=warehouse_id)
        except Warehouse.DoesNotExist:
            return Response({"error":"Warehouse not found"}, status=status.HTTP_404_NOT_FOUND)
        
        inventory_level, created = InventoryLevel.objects.get_or_create(
            warehouse=warehouse,
            product=product,
            defaults={"quantity_on_hand":0}
        )

        inventory_level.quantity_on_hand += int(adjustment)
        if inventory_level.quantity_on_hand < 0:
            return Response({"error":"Inventory cannot go below zero unit!"}, status=status.HTTP_400_BAD_REQUEST)
        
        inventory_level.save()

        return Response({
            "message":"Stock successfully updated",
            "sku":product.sku,
            "warehouse":warehouse.code,
            "new_quantity":inventory_level.quantity_on_hand
        }, status=status.HTTP_200_OK)

