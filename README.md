# OrderService — Microservice for Order Management
OrderService is a scalable Django REST Framework (DRF) microservice responsible for managing customer orders in a distributed e-commerce ecosystem.
It exposes REST APIs for core order handling and communicates with other microservices via API calls.

---

# Table of Contents
 - [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Features](#features)
- [API Reference (Quick)](#api-reference-quick)
- [Environment & Configuration](#environment--configuration)
- [Running the Service](#running-the-service)
- [Kubernetes Deployment & Prometheus Setup](#kubernetes-deployment--prometheus-setup)
-  [Database Schema](#database-schema)
- [Contact](#contact)


---

## Project Overview

- OrderService manages the entire order lifecycle, including:

- Creation of orders

- Listing orders

- Updating orders

- Getting order details

- Order history for each customer (shows payment, order, and shipping status)

---

## Tech Stack

| Component       | Technology / Version |
|-----------------|-------------------|
| Backend         | Django 5.0 + Django REST Framework 3.15 |
| Python          | 3.11 |
| Database        | PostgreSQL 15 |
| Monitoring      | Prometheus (`/metrics`) |
| Containerization| Docker + Docker Compose |
| Orchestration   | Kubernetes (manifests under `k8s/`) |
| Server          | Gunicorn WSGI |

---

# Project structure
```
OrderService/
├── Dockerfile                  # Build instructions for containerization
├── docker-compose.yml          # Local multi-container orchestration
├── prometheus.yml              # Prometheus scrape config (local/standalone)
├── requirements.txt            # Python dependencies
├── init.sql                    # SQL schema and migrations for Postgres
├── seed_db.py                  # DB seeding from CSV files
├── manage.py                   # Django command-line entry point
├── .env                        # Local/dev environment variable config
├── Seed Data/                  # Prebuilt CSV samples for database seeding
│   ├── eci_orders.csv
│   └── eci_order_items.csv
├── k8s/                        # Kubernetes manifests for cluster deployment
│   ├── order-service-configmap.yaml   # Env vars/config settings for OrderService
│   ├── order-service-deployment.yaml  # Main API deployment & Service
│   ├── postgres-deployment.yaml       # Postgres DB Deployment & Service
│   ├── prometheus-configmap.yaml      # Prometheus YAML config
│   ├── prometheus-deployment.yaml     # Prometheus Deployment
│   └── prometheus-service.yaml        # NodePort Service for Prometheus dashboard
├── OrderService/               # Django project configuration
│   ├── settings.py
│   └── urls.py
└── ordersapp/                  # Main Django app
    ├── models.py               # DB models for orders and items
    ├── serializer.py           # DRF serialization logic
    ├── views.py                # API implementation for endpoints
    ├── Services/               # Service clients for connecting Inventory, Payment, Shipping
    │   ├── inventory_client.py
    │   ├── order_services.py
    │   ├── payment_client.py
    │   └── shipping_client.py
    ├── Status/                 # ENUMs for status management
    ├── static/                 # Static assets (CSS, JS, images)
    └── templates/              # HTML templates if UI rendered
```
---

## Features

- Create, view, list, filter, and search orders

- Search orders by product, customer, or order ID

- Integrates with Inventory, Payment, and Shipping services via ordersapp/Services/ API clients

- Exposes Prometheus metrics at /metrics endpoint for monitoring

- Toggle between mock and real microservice integrations via .env settings 

---

## API Reference (Quick)

| Method | Endpoint                                    | Description                                                        |
|--------|---------------------------------------------|--------------------------------------------------------------------|
| GET    | /v1/orders/                                 | List all orders                                                    |
| POST   | /v1/orders/create/                          | Create a new order                                                 |
| POST   | /v1/orders/{id}/cancel/                     | Cancel an order                                                    |
| GET    | /v1/orders/{id}/details/                    | Get details for a specific order                                   |
| GET    | /v1/orders/my-orders/{customer_id}/         | View orders for a particular customer (filtering, sorting, pagination) |
| GET    | /health/                                    | Health/liveness check for service                                  |
| GET    | /orders-doc/                                | Swagger/OpenAPI API documentation                                  |
| GET    | /metrics                                    | Prometheus metrics endpoint                                        |

 - See /orders-doc/ for how requests and responses are structured.
---

## Environment & Configuration
- All major service and DB settings are stored in .env (for Compose/local) or in Kubernetes ConfigMaps. Example settings:
```
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,order-service
DEBUG=True
DB_NAME=order_db
DB_USER=postgres
DB_PASSWORD=root
DB_HOST=order-db
DB_PORT=5432

USER_SERVICE_URL=http://user-service:8000
INVENTORY_SERVICE_URL=http://inventory-service:8002
PAYMENT_SERVICE_URL=http://payment-service:8003
SHIPPING_SERVICE_URL=http://shipping-service:8004

USE_MOCK_USER=True
USE_MOCK_INVENTORY=True
USE_MOCK_PAYMENT=True
USE_MOCK_SHIPPING=True
SEED_PATH=./Seed Data
```
---

## Running the Service
Local Environment
```bash
# 1. Create & activate virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up .env file as above

# 4. Create database tables
python manage.py migrate

# 5. (Optional) Seed sample data
python seed_db.py

# 6. Start service
python manage.py runserver 0.0.0.0:8001
# Or (for production):
gunicorn OrderService.wsgi:application --bind 0.0.0.0:8001
```

## Docker (recommended)

```bash
# Build and run containers for OrderService and Postgres
docker compose up --build

# Stop all containers
docker compose down

# Remove containers & volumes
docker compose down -v

# Rebuild after code/dependency changes
docker compose up --build

# See service status
docker ps

# The API is available at http://localhost:8001/

```

## Kubernetes Deployment & Prometheus Setup

```bash
# Start local cluster
minikube start

# (Optional) Enable ingress
minikube addons enable ingress

# Deploy database
kubectl apply -f k8s/postgres-deployment.yaml

# Deploy OrderService
kubectl apply -f k8s/order-service-configmap.yaml
kubectl apply -f k8s/order-service-deployment.yaml

# Deploy monitoring
kubectl apply -f k8s/prometheus-configmap.yaml
kubectl apply -f k8s/prometheus-deployment.yaml
kubectl apply -f k8s/prometheus-service.yaml

# List pods/services
kubectl get pods
kubectl get svc

# Access OrderService or Prometheus dashboards
minikube service order-service
minikube service prometheus

# Stop and remove cluster
minikube stop
minikube delete

```

## Database Scehma
```sql
-- Orders Table
CREATE TABLE IF NOT EXISTS public.ordersapp_order
(
    order_id bigint NOT NULL DEFAULT nextval('ordersapp_order_order_id_seq'::regclass), -- Unique order identifier
    customer_id bigint NOT NULL,        -- Customer reference
    order_status character varying(20) NOT NULL DEFAULT 'PENDING', -- Order status
    payment_status character varying(20) NOT NULL DEFAULT 'PENDING', -- Payment status
    order_total numeric(10,2) NOT NULL DEFAULT 0.00, -- Total value of order
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP, -- Timestamp
    CONSTRAINT ordersapp_order_pkey PRIMARY KEY (order_id)
);

-- Order Items Table
CREATE TABLE IF NOT EXISTS public.ordersapp_orderitem
(
    order_item_id bigint NOT NULL DEFAULT nextval('ordersapp_orderitem_order_item_id_seq'::regclass), -- Unique item identifier
    order_id bigint NOT NULL,                -- Related order
    product_id bigint NOT NULL,              -- Product reference
    sku character varying(100) NOT NULL,     -- Stock keeping unit
    quantity integer NOT NULL DEFAULT 1,     -- Number of items
    unit_price numeric(10,2) NOT NULL DEFAULT 0.00, -- Price per item
    CONSTRAINT ordersapp_orderitem_pkey PRIMARY KEY (order_item_id),
    CONSTRAINT ordersapp_orderitem_order_id_fkey FOREIGN KEY (order_id)
        REFERENCES public.ordersapp_order (order_id) ON DELETE CASCADE
);
# All columns and constraints include clarifying comments for developers.
```


# Contact

- P Naveen Prabhath | 2024tm93544@wilp.bits-pilani.ac.in





