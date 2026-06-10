from django.db import migrations

def seed_system_permissions(apps, schema_editor):
    Permission = apps.get_model('users', 'Permission')
    
    # Define our core granular system permissions
    core_permissions = [
        # Order Domain Permissions
        {"name": "View Orders", "codename": "orders:view", "description": "Can view historical invoices and order lists."},
        {"name": "Create Orders", "codename": "orders:create", "description": "Can place high-concurrency B2B wholesale orders."},
        {"name": "Export Order Reports", "codename": "orders:export_report", "description": "Can trigger asynchronous compilation of CSV analytical logs."},
        
        # We can add placeholders here for the other modules we are building next
        {"name": "View Customers", "codename": "customers:view", "description": "Can view customer profiles and transaction histories."},
        {"name": "Manage Customers", "codename": "customers:manage", "description": "Can create, update, or delete customer records."},
        {"name": "View Audit Logs", "codename": "audit:view", "description": "Can view system mutation logs for security compliance."},
    ]
    
    for perm in core_permissions:
        Permission.objects.update_or_create(
            codename=perm["codename"],
            defaults={"name": perm["name"], "description": perm["description"]}
        )

def remove_system_permissions(apps, schema_editor):
    Permission = apps.get_model('users', 'Permission')
    Permission.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'), # Overwrite with the actual name of your initial users migration
    ]

    operations = [
        migrations.RunPython(seed_system_permissions, reverse_code=remove_system_permissions),
    ]