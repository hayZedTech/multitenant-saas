from django.db import models
from apps.tenants.models import TenantModel
from django.core.exceptions import ValidationError

class Warehouse(TenantModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, help_text="Unique code for the warehouse")
    address = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("tenant", "code")

    def __str__(self):
        return f"{self.name} {self.code}"
    
class Product(TenantModel):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, help_text="Stock Keeping Unit:Unique product code")
    description = models.TextField(null=True, blank=True)
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="bulk price")
    weight_kg = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together= ("tenant", "sku")

    def __str__(self):
        return f"{self.name} {self.sku}"
    
class InventoryLevel(TenantModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventory_balances")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stocks")
    quantity_on_hand = models.IntegerField(default=0)
    reorder_point = models.IntegerField(default=10, help_text="minimum number of qauntity before reorder is triggered")

    class Meta:
        unique_together = ("tenant", "product", "warehouse")

    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse.code} : {self.quantity_on_hand}"

    def clean(self):
        if self.product.tenant != self.warehouse.tenant:
            raise ValidationError("warehouse and product must have the same tenant!")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

