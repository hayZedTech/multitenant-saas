# apps/orders/services.py

from django.db import transaction
from django.core.exceptions import ValidationError
from apps.orders.models import Order, OrderItem, Customer
from apps.inventory.models import InventoryLevel, Product, Warehouse
from apps.tenants.utils import get_current_tenant  # 👈 Added your thread-local utility

class OrderPlacementService:
    """Handles core atomic checkout logic, tier discounts, and race-condition row prevention."""
    
    @staticmethod
    @transaction.atomic
    def create_b2b_order(customer_id, warehouse_id, order_items_data):
        """
        Creates an order line-by-line while locking active inventory cells 
        via PostgreSQL SELECT FOR UPDATE to prevent data race conditions.
        
        order_items_data structure: [{"product_id": 1, "quantity": 10}, ...]
        """
        # 1. Fetch the thread-local active tenant context
        current_tenant = get_current_tenant()
        if not current_tenant:
            raise ValidationError("Operational context error: No active tenant detected.")

        # 2. Fetch domain actors within current tenant boundary with strict cross-tenant isolation guards
        try:
            # 🔒 STRICTOR TENANT GUARD: Force explicit filtering against the active tenant context
            customer = Customer.objects.get(pk=customer_id, tenant=current_tenant)
            warehouse = Warehouse.objects.get(pk=warehouse_id, tenant=current_tenant)
        except Customer.DoesNotExist:
            raise ValidationError("Access Denied: The requested customer record does not exist for this tenant.")
        except Warehouse.DoesNotExist:
            raise ValidationError("Access Denied: The requested warehouse record does not exist for this tenant.")
        except ValidationError as e:
            raise ValidationError(f"Invalid actor parameters: {str(e)}")

        if not order_items_data:
            raise ValidationError("An order must contain at least one line item entry.")

        # 3. Instantiate base order model shell (TenantModel hooks handle tenant assignment on save)
        order = Order.objects.create(
            customer=customer,
            warehouse=warehouse,
            status='PENDING',
            total_amount=0.00
        )

        running_total = 0

        # 4. Process lines and apply database row locks
        for item in order_items_data:
            product_id = item.get("product_id")
            quantity = int(item.get("quantity"))

            if quantity <= 0:
                raise ValidationError("Quantity requested must be a positive integer value.")

            try:
                # 🔒 STRICTOR TENANT GUARD: Ensure the target product belongs to the active tenant catalog
                product = Product.objects.get(pk=product_id, tenant=current_tenant)
            except Product.DoesNotExist:
                raise ValidationError(f"Product ID {product_id} not found in tenant catalog.")

            # 🔥 THE CONCURRENCY SHIELD: select_for_update() locks this row in PostgreSQL.
            try:
                stock_balance = InventoryLevel.objects.select_for_update().get(
                    product=product,
                    warehouse=warehouse,
                    tenant=current_tenant  # 🔒 Passing current tenant validation to match your model manager
                )
            except InventoryLevel.DoesNotExist:
                raise ValidationError(f"Product {product.sku} has no inventory configured at warehouse {warehouse.code}.")

            # 5. Enforce stock limit integrity checks
            if stock_balance.quantity_on_hand < quantity:
                raise ValidationError(
                    f"Insufficient Stock! Requested {quantity} units of {product.sku}, "
                    f"but only {stock_balance.quantity_on_hand} are available in warehouse {warehouse.code}."
                )

            # 6. Calculate customer tier bulk B2B discounts
            base_price = product.wholesale_price
            discount_multiplier = (100 - customer.tier_discount_percentage) / 100
            final_unit_price = base_price * discount_multiplier

            # 7. Allocate order item and deduct stock safely
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=final_unit_price
            )

            stock_balance.quantity_on_hand -= quantity
            stock_balance.save()

            running_total += (final_unit_price * quantity)

        # 8. Write back calculated ledger matrix onto root order node
        order.total_amount = running_total
        order.status = 'PROCESSING'
        order.save()

        return order