from django.db import transaction
from django.core.exceptions import ValidationError
from apps.orders.models import Order, OrderItem, Customer
from apps.inventory.models import InventoryLevel, Product, Warehouse

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
        # 1. Fetch domain actors within current tenant boundary
        try:
            customer = Customer.objects.get(pk=customer_id)
            warehouse = Warehouse.objects.get(pk=warehouse_id)
        except (Customer.DoesNotExist, Warehouse.DoesNotExist) as e:
            raise ValidationError(f"Invalid actor parameters: {str(e)}")

        if not order_items_data:
            raise ValidationError("An order must contain at least one line item entry.")

        # 2. Instantiate base order model shell
        order = Order.objects.create(
            customer=customer,
            warehouse=warehouse,
            status='PENDING',
            total_amount=0.00
        )

        running_total = 0

        # 3. Process lines and apply database row locks
        for item in order_items_data:
            product_id = item.get("product_id")
            quantity = int(item.get("quantity"))

            if quantity <= 0:
                raise ValidationError("Quantity requested must be a positive integer value.")

            try:
                product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                raise ValidationError(f"Product ID {product_id} not found in tenant catalog.")

            # 🔥 THE CONCURRENCY SHIELD: select_for_update() locks this row in PostgreSQL.
            # Any concurrent request trying to read or modify this specific stock cell
            # will hang until this code blocks hits a commit or a rollback error.
            try:
                stock_balance = InventoryLevel.objects.select_for_update().get(
                    product=product,
                    warehouse=warehouse
                )
            except InventoryLevel.DoesNotExist:
                raise ValidationError(f"Product {product.sku} has no inventory configured at warehouse {warehouse.code}.")

            # 4. Enforce stock limit integrity checks
            if stock_balance.quantity_on_hand < quantity:
                raise ValidationError(
                    f"Insufficient Stock! Requested {quantity} units of {product.sku}, "
                    f"but only {stock_balance.quantity_on_hand} are available in warehouse {warehouse.code}."
                )

            # 5. Calculate customer tier bulk B2B discounts
            base_price = product.wholesale_price
            discount_multiplier = (100 - customer.tier_discount_percentage) / 100
            final_unit_price = base_price * discount_multiplier

            # 6. Allocate order item and deduct stock safely
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=final_unit_price
            )

            stock_balance.quantity_on_hand -= quantity
            stock_balance.save()

            running_total += (final_unit_price * quantity)

        # 7. Write back calculated ledger matrix onto root order node
        order.total_amount = running_total
        order.status = 'PROCESSING'
        order.save()

        return order