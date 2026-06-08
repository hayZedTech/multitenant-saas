import pytest
from rest_framework.test import APIClient
from apps.tenants.models import Tenant, User
from apps.inventory.models import Product, Warehouse

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def setup_multitenant_data(db):
    """Sets up two completely separate tenants, users, and warehouse catalogs."""
    # Tenant A Setup
    tenant_a = Tenant.objects.create(name="Alpha Logistics", company_domain="alpha.co")
    user_a = User.objects.create_user(username="alpha_admin", password="password123", tenant=tenant_a)
    warehouse_a = Warehouse.objects.create(name="Lagos Hub", code="LOS-01", address="Lagos", tenant=tenant_a)
    product_a = Product.objects.create(name="Industrial Pumps", sku="PUMP-001", wholesale_price=5000.00, tenant=tenant_a)

    # Tenant B Setup
    tenant_b = Tenant.objects.create(name="Beta Distributors", company_domain="beta.co")
    user_b = User.objects.create_user(username="beta_admin", password="password123", tenant=tenant_b)
    warehouse_b = Warehouse.objects.create(name="Ota Hub", code="OTA-01", address="Ota", tenant=tenant_b)
    product_b = Product.objects.create(name="Steel Rods", sku="ROD-99", wholesale_price=1200.00, tenant=tenant_b)

    return {
        "tenant_a": tenant_a, "user_a": user_a, "product_a": product_a,
        "tenant_b": tenant_b, "user_b": user_b, "product_b": product_b
    }


@pytest.mark.django_db
def test_tenant_isolation_on_product_list_endpoint(api_client, setup_multitenant_data):
    """Verifies that a tenant can only view their own catalog items on list endpoints."""
    user_a = setup_multitenant_data["user_a"]
    product_a = setup_multitenant_data["product_a"]
    product_b = setup_multitenant_data["product_b"]

    # Authenticate as Tenant A
    api_client.force_authenticate(user=user_a)
    
    response = api_client.get("/api/v1/products/")
    
    assert response.status_code == 200
    # The response list must include Tenant A's product
    assert any(item["sku"] == product_a.sku for item in response.data)
    # CRITICAL: The response must NEVER contain Tenant B's product data
    assert not any(item["sku"] == product_b.sku for item in response.data)


@pytest.mark.django_db
def test_cross_tenant_detail_access_is_blocked(api_client, setup_multitenant_data):
    """Verifies that direct detail lookups for other tenant IDs return 404 Not Found."""
    user_a = setup_multitenant_data["user_a"]
    product_b = setup_multitenant_data["product_b"] # Belongs to Tenant B

    # Authenticate as Tenant A
    api_client.force_authenticate(user=user_a)
    
    # Attempt to target Tenant B's resource directly via ID
    response = api_client.get(f"/api/v1/products/{product_b.id}/")
    
    # The infrastructure must treat it as non-existent to protect system architecture info
    assert response.status_code == 404