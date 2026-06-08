# Headless Multi-Tenant SaaS B2B Inventory & Order Management API Engine

A high-performance, enterprise-grade REST API built with Django and Django REST Framework (DRF). This backend platform utilizes a **Shared Database, Shared Schema (Row-Level Isolation)** architecture to securely serve multiple independent business tenants from a single deployment instance.

The engine features strict data isolation guards, pessimistic database concurrency shields to prevent stock overselling, and decoupled asynchronous task execution for long-running data workflows.

## 🚀 Live Demo & Documentation
* **Live API Root:** [https://multitenant-saas-byx3.onrender.com/api/v1/](https://multitenant-saas-byx3.onrender.com/api/v1/)
* **Interactive Swagger UI:** [https://multitenant-saas-byx3.onrender.com/api/v1/docs/](https://multitenant-saas-byx3.onrender.com/api/v1/docs/)


---

## 🚀 Core Features & Architectural Safeguards

* **Automated Tenant Isolation:** Powered by custom Django Database Managers and thread-local middleware. The active tenant context is automatically extracted from incoming JWT tokens, ensuring that no developer can accidentally leak or query cross-tenant data.
* **Race-Condition Prevention:** Implements pessimistic row-level locking via PostgreSQL `SELECT FOR UPDATE` inside the transactional service layers. Concurrent wholesale checkout actions queue up safely to ensure inventory balances never drop below zero.
* **Asynchronous Background Workloads:** Integrates Celery and Redis to handle non-blocking, heavy computing operations, such as generating massive historical CSV reports and running fault-tolerant outbound webhook dispatch systems.
* **Self-Documenting API Hub:** Fully compliant with the OpenAPI 3.0 specification. Interactive Swagger UI endpoints are generated automatically via `drf-spectacular`, complete with integrated JWT Bearer authorization toolbars.
* **Robust Test Pipeline:** Includes an automated integration test suite driven by `pytest` to continuously verify multi-tenant row security boundaries.

---

## 🛠️ Technology Stack

* **Framework:** Django 5.x & Django REST Framework (DRF)
* **Database:** PostgreSQL (Required for transactional integrity and row locking)
* **Task Broker:** Celery & Redis
* **Authentication:** SimpleJWT (JSON Web Tokens)
* **Documentation:** drf-spectacular (OpenAPI 3.0 / Swagger UI)
* **Testing Suite:** Pytest & Pytest-Django

---

## 📂 Repository Structure

```text
multitenant_saas/
│
├── core/                         # Project Configuration Root
│   ├── settings.py               # Database, DRF, Celery, & Redis configs
│   ├── urls.py                   # Global routing & Swagger declarations
│   └── celery.py                 # Celery engine initialization
│
├── apps/                         # Modular Functional Sub-Apps
│   ├── tenants/                  # Tenant Onboarding & Context Layer
│   │   ├── middleware.py         # Thread-local tenant scoping middleware
│   │   └── models.py             # Custom User, Tenant, and TenantModel abstract base
│   │
│   ├── inventory/                # SKU Management & Warehouse Tracking
│   │   ├── models.py             # Warehouse, Product, and InventoryLevel schemas
│   │   └── views.py              # Isolated multi-facility stock controllers
│   │
│   └── orders/                   # Order Processing & Service Layer
│       ├── services.py           # Concurrency-safe atomic checkout logic
│       ├── tasks.py              # Celery background workers (CSV & Webhooks)
│       └── views.py              # REST endpoints and custom action nodes
│
├── pytest.ini                    # Automated test configuration
├── requirements.txt              # Project dependencies
└── manage.py