# OrderService — Microservice for Order Management

OrderService is a **scalable Django REST Framework (DRF) microservice** responsible for managing customer orders in a distributed e-commerce ecosystem.  
It exposes REST APIs and communicates with other microservices via API calls.

---

## Table of Contents

- Project Overview 
- Tech Stack 
- Project Structure
- Features
- API Reference (Quick)
- Environment & Configuration
- Running the Service 
- Kubernetes Deployment & Prometheus Setup
- Database Schema
- Contact 

---

## Project Overview

OrderService handles the **entire order lifecycle**, including:

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
├── Dockerfile
├── docker-compose.yml
├── prometheus.yml
├── requirements.txt
├── init.sql
├── seed_db.py
├── manage.py
├── .env                   # Your environment variables
├── Seed Data/             # CSV seed files
│   ├── eci_orders.csv
│   └── eci_order_items.csv
├── k8s/                   # Kubernetes deployment/config files
│   ├── order-service-configmap.yaml
│   ├── order-service-deployment.yaml
│   ├── postgres-deployment.yaml
│   ├── prometheus-configmap.yaml
│   ├── prometheus-deployment.yaml
│   └── promethues-service.yaml
├── OrderService/          # Django project folder
│   ├── settings.py
│   └── urls.py
└── ordersapp/             # Django app
    ├── models.py
    ├── serializer.py
    ├── views.py
    ├── Services/          # Service clients for inter-service communication
    │   ├── inventory_client.py
    │   ├── order_services.py
    │   ├── payment_client.py
    │   └── shipping_client.py
    ├── Status/            # Enums for status management
    │   ├── order_status.py
    │   ├── payment_status.py
    │   └── shipping_status.py
    ├── static/            # Frontend assets
    │   └── ordersapp/
    │       ├── css/
    │       ├── js/
    │       └── Images/
    └── templates/         # Django HTML templates
```
---

## Features

- Create, view, list, and filter orders  
- Search orders by product, customer, or order ID  
- Integrates with Inventory, Payment, and Shipping services via clients in `ordersapp/Services/`  
- Prometheus metrics available at `/metrics`  

---

## API Reference (Quick)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET    | [http://localhost:8001/v1/orders/](http://localhost:8001/v1/orders/) | List all orders | ✅ |
| POST   | [http://localhost:8001/v1/orders/create/](http://localhost:8001/v1/orders/create/) | Create a new order | ✅ |
| POST   | [http://localhost:8001/v1/orders/{id}/cancel/](http://localhost:8001/v1/orders/{id}/cancel/) | Cancel an order | ✅ |
| GET    | [http://localhost:8001/v1/orders/{id}/details/](http://localhost:8001/v1/orders/{id}/details/) | Get order details | ✅ |
| GET    | [http://localhost:8001/v1/orders/my-orders/{customer_id}/](http://localhost:8001/v1/orders/my-orders/{customer_id}/) | View order history (filters, sort, pagination) | ✅ |
| GET    | [http://localhost:8001/health/](http://localhost:8001/health/) | Health check | ❌ |
| GET    | [http://localhost:8001/orders-doc/](http://localhost:8001/orders-doc/) | Swagger API documentation | ❌ |

---

## Environment Configuration

---

## Local Environment
```bash
# Create & activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables in .env

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver 0.0.0.0:8001

# Or use Gunicorn for production-like deployment
gunicorn OrderService.wsgi:application --bind 0.0.0.0:8001
```

## Docker (recommended)

```bash
# Build and start containers (initial run)
docker compose up --build

# Stop running containers gracefully
docker compose down

# Stop containers but keep volumes
docker compose down -v

# Restart containers after stopping
docker compose up

# Rebuild containers after code changes
docker compose up --build

# Check running containers
docker ps

# Access the service in browser
# http://localhost:8001/
```

## Kubernetes & Prometheus Basic Setup

```bash
# Start Minikube cluster
minikube start

# Enable ingress (optional, if using ingress rules)
minikube addons enable ingress

# Deploy Postgres
kubectl apply -f k8s/postgres-deployment.yaml

# Deploy OrderService
kubectl apply -f k8s/order-service-deployment.yaml

# Deploy Prometheus
kubectl apply -f k8s/prometheus-deployment.yaml

# Apply ConfigMaps (if not included in deployments)
kubectl apply -f k8s/order-service-configmap.yaml
kubectl apply -f k8s/prometheus-configmap.yaml

# Apply Prometheus Service
kubectl apply -f k8s/promethues-sevice.yaml

# Optional: Apply ingress rules
# kubectl apply -f k8s/ingress.yaml

# Check pods and services
kubectl get pods
kubectl get svc

# Access Minikube service in browser
minikube service order-service   # Opens OrderService URL
minikube service prometheus      # Opens Prometheus dashboard

# To stop Minikube
minikube stop

# To delete Minikube cluster
minikube delete
```

# Database Scehma
```
# Orders Table
CREATE TABLE IF NOT EXISTS public.ordersapp_order
(
    order_id bigint NOT NULL DEFAULT nextval('ordersapp_order_order_id_seq'::regclass),
    customer_id bigint NOT NULL,
    order_status character varying(20) COLLATE pg_catalog."default" NOT NULL DEFAULT 'PENDING'::character varying,
    payment_status character varying(20) COLLATE pg_catalog."default" NOT NULL DEFAULT 'PENDING'::character varying,
    order_total numeric(10,2) NOT NULL DEFAULT 0.00,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ordersapp_order_pkey PRIMARY KEY (order_id)
)
# Order Items Table
CREATE TABLE IF NOT EXISTS public.ordersapp_orderitem
(
    order_item_id bigint NOT NULL DEFAULT nextval('ordersapp_orderitem_order_item_id_seq'::regclass),
    order_id bigint NOT NULL,
    product_id bigint NOT NULL,
    sku character varying(100) COLLATE pg_catalog."default" NOT NULL,
    quantity integer NOT NULL DEFAULT 1,
    unit_price numeric(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT ordersapp_orderitem_pkey PRIMARY KEY (order_item_id),
    CONSTRAINT ordersapp_orderitem_order_id_fkey FOREIGN KEY (order_id)
        REFERENCES public.ordersapp_order (order_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
```


# Contact

 - P Naveen Prabhath | 2024tm93544@wilp.bits-pilani.ac.in





