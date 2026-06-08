from django.db import models
from apps.tenants.models import TenantModel
from apps.inventory.models import Product, Warehouse

class Customer(TenantModel):
    """Represents a corporate B2B buyer purchasing goods from the active tenant."""
    company_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    tier_discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, 
        help_text="Custom wholesale percentage discount automatically applied to this buyer's orders"
    )

    class Meta:
        unique_together = ('tenant', 'email')

    def __str__(self):
        return self.company_name


class Order(TenantModel):
    """Represents a wholesale invoice/purchase order raised by a customer."""
    STATUS_CHOICES = (
        ('PENDING', 'Pending Allocation'),
        ('PROCESSING', 'Processing in Warehouse'),
        ('DISPATCHED', 'Dispatched for Delivery'),
        ('CANCELLED', 'Cancelled/Stock Returned'),
    )

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="orders", help_text="Source warehouse for order allocation")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.company_name} [{self.status}]"


class OrderItem(TenantModel):
    """A single product row line item within a parent B2B order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_lines")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Price locked at point of checkout purchase")

    def __str__(self):
        return f"{self.quantity}x {self.product.sku} on Order #{self.order.id}"