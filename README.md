OrderService — Microservice for Order Management

A scalable Django REST Framework (DRF) microservice responsible for managing customer orders in a distributed e-commerce ecosystem.
Exposes REST APIs for external consumption and communicates with other microservices (UserService, InventoryService, PaymentService, ShippingService) via internal service clients.

Table of contents

Project Overview

Tech Stack

Repository Structure

Features

API Reference (quick)

Authentication

Environment & Configuration

Running the service (Docker / Local)

Kubernetes Deployment

Monitoring

Development notes & conventions

Troubleshooting

Contributing

Contact / Author

License

Project overview

OrderService handles order lifecycle: creation, retrieval, filtering, searching, cancellation and tracking.
Business logic and interservice communication are implemented in service clients under ordersapp/Services/. The service is JWT-protected and instrumented for Prometheus.

Tech stack

Backend: Django 5.0 + Django REST Framework 3.15

Python: 3.11

Database: PostgreSQL 15

Auth: JWT via djangorestframework-simplejwt (tokens issued by UserService)

Monitoring: Prometheus (/metrics)

Containerization: Docker + Docker Compose

Orchestration: Kubernetes (manifests under k8s/)

Server: Gunicorn WSGI

Repository structure
OrderService/
├── package.json
├── ordersapp/
│   ├── Status/
│   │   ├── order_status.py
│   │   ├── shipping_status.py
│   │   └── payment_status.py
│   ├── static/
│   │   ├── css/style.css
│   │   ├── images/
│   │   └── js/order.js
│   ├── Services/
│   │   ├── inventory_client.py
│   │   ├── order_services.py
│   │   ├── payment_client.py
│   │   └── shipping_client.py
│   ├── templates/orderapp/
│   │   ├── order_filters.html
│   │   └── order_history.html
│   ├── decorators.py
│   ├── models.py
│   ├── serializer.py
│   ├── apps.py
│   ├── admin.py
│   └── views.py
├── k8s/
│   ├── ingress.yaml
│   ├── orderservice.yaml
│   ├── postgres.yaml
│   └── prometheus.yml
├── OrderService/          # Django project
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── .env
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
└── README.md

Features
Core responsibilities

Create, view, list and filter orders

Search orders by product, customer or order ID

Integrates with Inventory, Payment and Shipping services via clients in ordersapp/Services/

JWT-protected endpoints (except health and docs)

Prometheus metrics at /metrics

Key API endpoints (base path: /v1/)
Method	Path	Description	Auth
GET	/v1/orders/	List all orders	✅
POST	/v1/orders/create/	Create a new order	✅
POST	/v1/orders/{id}/cancel/	Cancel an order	✅
GET	/v1/orders/{id}/details/	Get order details	✅
GET	/v1/orders/my-orders/{customer_id}/	View order history (filters, sort, pagination)	✅
GET	/health/	Health check	❌
GET	/orders-doc/	Swagger API docs	❌
API examples

List orders:

curl -X GET http://localhost:8001/v1/orders/ \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json"


Create order:

curl -X POST http://localhost:8001/v1/orders/create/ \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 5,
    "items": [
      {"sku":"SKU123", "quantity":2, "unit_price":100.0},
      {"sku":"SKU456", "quantity":1, "unit_price":50.0}
    ]
  }'


View order history (example with query params):

GET /v1/orders/my-orders/5/?status_filter=shipped&payment_filter=paid&sort_by=created_at&page=1&page_size=20

Authentication

All protected endpoints require a JWT in the Authorization header:

Authorization: Bearer <your_jwt_token>


Tokens are expected to be issued by UserService.

Environment & configuration

Create a .env in project root (example):

DB_NAME=ordersdb
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432
SECRET_KEY=a@w-vlr#hv&y68_n7f$a4$&+p&^cay-=pw0r^%xjs(w*0@_(5x)


Add any service-specific environment variables (e.g., INVENTORY_SERVICE_URL, PAYMENT_SERVICE_URL, SHIPPING_SERVICE_URL, JWT public key/issuer settings) to .env or your deployment config.

Running the service
Docker (recommended for local dev)

Build and run:

docker compose up --build


Check containers:

docker ps


Access:

http://localhost:8001/

Local (virtualenv)

create venv & install:

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt


configure .env (or env vars)

run migrations & start:

python manage.py migrate
python manage.py runserver 0.0.0.0:8001


Or use Gunicorn (production-like):

gunicorn OrderService.wsgi:application --bind 0.0.0.0:8001

Kubernetes deployment

Manifests live under k8s/:

postgres.yaml — Postgres StatefulSet / PVC / Service

orderservice.yaml — Deployment / Service for orderservice

ingress.yaml — Ingress rules (if used)

prometheus.yml — Prometheus scrape config (snippet)

Deploy sequence (example):

kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/orderservice.yaml
kubectl apply -f k8s/ingress.yaml   # optional


Check:

kubectl get pods
kubectl get svc

Monitoring

Expose /metrics for Prometheus. Example scrape config (add to Prometheus prometheus.yml):

scrape_configs:
  - job_name: 'orderservice'
    static_configs:
      - targets: ['orderservice:8001']
    metrics_path: '/metrics'


Access metrics:

http://localhost:8001/metrics

Development notes & conventions

Business logic and interservice calls are in ordersapp/Services/ (e.g., inventory_client.py, payment_client.py). Prefer adding new interservice logic there.

Enums for statuses are maintained under ordersapp/Status/. Use these enums for validation and serialization.

Serializers in ordersapp/serializer.py contain the DRF serialization logic for orders.

Views in ordersapp/views.py expose the endpoints (DRF viewsets or APIViews).

Authentication decorator/helpers in ordersapp/decorators.py.
