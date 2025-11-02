# 🧾 OrderService — Microservice for Order Management

A scalable **Django REST Framework (DRF)** microservice responsible for managing customer orders in a distributed e-commerce system.  
It interacts with other services (**UserService**, **InventoryService**, etc.) through internal client logic and exposes **REST APIs** for external consumption.

---

## 📁 Project Structure

OrderService/
├── package.json
├── ordersapp/
│ ├── Status/ # Required status enums
│ │ ├── order_status.py
│ │ ├── shipping_status.py
│ │ └── payment_status.py
│ ├── static/ # Static assets (CSS, JS, images)
│ │ ├── css/
│ │ │ └── style.css
│ │ ├── images/
│ │ └── js/
│ │ └── order.js
│ ├── Services/ # Interservice logic
│ │ ├── inventory_client.py
│ │ ├── order_services.py
│ │ ├── payment_client.py
│ │ └── shipping_client.py
│ ├── templates/orderapp/ # HTML templates
│ │ ├── order_filters.html
│ │ └── order_history.html
│ ├── decorators.py # Authentication logic
│ ├── models.py
│ ├── serializer.py # Serializer for orders model
│ ├── apps.py
│ ├── admin.py
│ └── views.py
├── k8s/ # Kubernetes manifests
│ ├── ingress.yaml
│ ├── orderservice.yaml
│ ├── postgres.yaml
│ └── prometheus.yml
├── OrderService/
│ ├── init.py
│ ├── asgi.py
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
├── .env
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
└── README.md

markdown
Copy code

---

## ⚙️ Tech Stack

| Category | Technology |
|-----------|-------------|
| **Backend Framework** | Django 5.0 + Django REST Framework 3.15 |
| **Language** | Python 3.11 |
| **Database** | PostgreSQL 15 |
| **Authentication** | JWT via `djangorestframework-simplejwt` |
| **Monitoring** | Prometheus (`/metrics` endpoint) |
| **Containerization** | Docker + Docker Compose |
| **Orchestration** | Kubernetes (K8s manifests included) |
| **Server** | Gunicorn WSGI |

---

## 🧠 Service Features

### 🔹 Core Responsibilities
- Manage order creation, retrieval, filtering, and tracking.  
- Central business logic lives in **`client.py`**, handling interservice communication and DB operations.  
- RESTful views handle incoming requests via Django DRF.

### 🔹 Key Features

#### 🛒 Order Management
- Create, view, and list order history  
- Endpoint: `/v1/orders/my-orders/<customer_id>/`

#### 💳 Payment & Status
- Filter orders by payment or status  
- Supports sorting and pagination

#### 🔍 Search
- Search orders by product, customer, or order ID

#### ⚙️ Microservice Integration
- Communicates with Inventory, Payment, and Shipping via service clients  
- Each service maintains its own database (no shared tables)

#### 🔐 JWT Protected APIs
- All endpoints require authentication (except `/health/` and `/orders-doc/`)

#### 📈 Monitoring
- `/metrics` endpoint integrated with **Prometheus**

---

## 🧾 Order Service API

### 🌐 Base URL
http://<host>:8001/v1/

less
Copy code

### 🔐 Authentication
All endpoints (except `/health/` and `/orders-doc/`) require **JWT**.  
Include your token in the header:
Authorization: Bearer <your_jwt_token>

pgsql
Copy code

Tokens are issued by **UserService** upon login.

---

### 🚀 Endpoints Overview

| Method | Endpoint | Description | Auth |
|--------|-----------|--------------|------|
| GET | `/v1/orders/` | List all orders | ✅ |
| POST | `/v1/orders/create/` | Create a new order | ✅ |
| POST | `/v1/orders/{id}/cancel/` | Cancel an order | ✅ |
| GET | `/v1/orders/{id}/details/` | Get order details | ✅ |
| GET | `/v1/orders/my-orders/{customer_id}/` | View order history | ✅ |
| GET | `/health/` | Health check | ❌ |
| GET | `/orders-doc/` | Swagger API Docs | ❌ |

---

### 📦 1. List All Orders
```bash
GET /v1/orders/
Example:

bash
Copy code
curl -X GET http://localhost:8001/v1/orders/ \
-H "Authorization: Bearer <your_jwt_token>" \
-H "Content-Type: application/json"
🛒 2. Create a New Order
bash
Copy code
POST /v1/orders/create/
Request Body:

json
Copy code
{
  "customer_id": 5,
  "items": [
    {"sku": "SKU123", "quantity": 2, "unit_price": 100.0},
    {"sku": "SKU456", "quantity": 1, "unit_price": 50.0}
  ]
}
❌ 3. Cancel an Order
bash
Copy code
POST /v1/orders/{id}/cancel/
📘 4. Get Order Details
bash
Copy code
GET /v1/orders/{id}/details/
📜 5. View Order History
bash
Copy code
GET /v1/orders/my-orders/{customer_id}/
Supports filters like status_filter, payment_filter, and sort_by.

❤️ 6. Health Check
bash
Copy code
GET /health/
📖 7. Swagger API Docs
bash
Copy code
GET /orders-doc/
🧩 Service Dependencies
Service	Purpose
Inventory Service	Reserve and release stock
Payment Service	Charge and refund payments
Shipping Service	Manage shipment creation and tracking

🧰 Environment Variables
Create a .env file in the project root:

env
Copy code
DB_NAME=ordersdb
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432
SECRET_KEY=a@w-vlr#hv&y68_n7f$a4$&+p&^cay-=pw0r^%xjs(w*0@_(5x)
🐳 Docker Setup
🧱 Dockerfile
dockerfile
Copy code
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["gunicorn", "OrderService.wsgi:application", "--bind", "0.0.0.0:8001"]
🧩 Docker Compose
yaml
Copy code
version: '3.9'

services:
  db:
    image: postgres:15
    container_name: order_postgres
    restart: always
    environment:
      POSTGRES_DB: ordersdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - order_pgdata:/var/lib/postgresql/data

  orderservice:
    build: .
    container_name: orderservice
    command: gunicorn OrderService.wsgi:application --bind 0.0.0.0:8001
    environment:
      - DB_NAME=ordersdb
      - DB_USER=postgres
      - DB_PASSWORD=postgres
      - DB_HOST=db
      - DB_PORT=5432
      - SECRET_KEY=a@w-vlr#hv&y68_n7f$a4$&+p&^cay-=pw0r^%xjs(w*0@_(5x)
    ports:
      - "8001:8001"
    depends_on:
      - db

volumes:
  order_pgdata:
✅ Run locally:

bash
Copy code
docker compose up --build
✅ Check containers:

bash
Copy code
docker ps
✅ Access:

arduino
Copy code
http://localhost:8001/
☸️ Kubernetes Deployment
🗂️ order-deployment.yaml
(see your full YAML in repo)

Deploy using:

bash
Copy code
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/orderservice.yaml
Check status:

bash
Copy code
kubectl get pods
kubectl get svc
📊 Prometheus Monitoring
Expose /metrics for scraping.

Add to prometheus.yml:

yaml
Copy code
scrape_configs:
  - job_name: 'orderservice'
    static_configs:
      - targets: ['orderservice:8001']
    metrics_path: '/metrics'
Access metrics:

bash
Copy code
http://localhost:8001/metrics
🚀 Deployment Summary
Component	Tool	Description
🐍 Backend	Django + DRF	Core microservice logic
🐳 Container	Docker + Compose	Local deployment
☸️ Orchestration	Kubernetes	Cluster management
🧾 Database	PostgreSQL	Dedicated DB per service
🔐 Security	JWT	Auth via UserService
📈 Monitoring	Prometheus	Metrics collection
📘 Docs	Swagger UI	API testing interface

🧠 Author
P. Naveen Prabhath
2024tm93544@wilp.bits-pilani.ac.in
