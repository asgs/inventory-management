import os
import uuid
import logging
import time
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List, Optional
from datetime import datetime, timedelta

from mock_data import (
    inventory_items, orders, demand_forecasts, backlog_items,
    spending_summary, monthly_spending, category_spending,
    recent_transactions, purchase_orders
)
from models import (
    InventoryItem, Order, DemandForecast, BacklogItem, PurchaseOrder,
    CreatePurchaseOrderRequest, RestockingItem, RestockingRecommendation,
    CreateRestockingOrderRequest
)
from constants import (
    QUARTER_MAP, MONTH_TO_QUARTER, ORDER_STATUSES, PENDING_STATUSES,
    CATEGORIES, WAREHOUSES, VALID_MONTHS
)
from filters import filter_by_month, apply_filters, paginate

# --- Configuration ---
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8001"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# --- Logging ---
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("inventory-api")

# --- App ---
app = FastAPI(title="Factory Inventory Management System")


# --- Security headers middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


# --- Request logging middleware ---
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 1)
        logger.info("%s %s -> %s (%sms)", request.method, request.url.path, response.status_code, duration_ms)
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


# --- Validation helpers ---
def validate_filter_param(name: str, value: Optional[str], allowed: set) -> None:
    """Validate a filter parameter against allowed values. Raises 400 if invalid."""
    if value and value != 'all':
        if value not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {name}: '{value}'. Allowed values: {sorted(allowed)}"
            )


def validate_month_param(month: Optional[str]) -> None:
    """Validate month parameter (YYYY-MM or Q#-YYYY format)."""
    if month and month != 'all':
        if month.startswith('Q'):
            if month not in QUARTER_MAP:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid quarter: '{month}'. Allowed: {sorted(QUARTER_MAP.keys())}"
                )
        elif month not in VALID_MONTHS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid month: '{month}'. Expected format: YYYY-MM (e.g. 2025-01)"
            )


# In-memory store for restocking orders
restocking_orders = []

logger.info("Server starting with %d inventory items, %d orders", len(inventory_items), len(orders))


# --- API endpoints ---

@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/inventory")
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None
):
    """Get all inventory items with optional filtering and pagination"""
    validate_filter_param("warehouse", warehouse, WAREHOUSES)
    validate_filter_param("category", category, CATEGORIES)
    filtered = apply_filters(inventory_items, warehouse, category)
    return paginate(filtered, page, page_size)


@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.get("/api/orders")
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None
):
    """Get all orders with optional filtering and pagination"""
    validate_filter_param("warehouse", warehouse, WAREHOUSES)
    validate_filter_param("category", category, CATEGORIES)
    validate_filter_param("status", status, ORDER_STATUSES)
    validate_month_param(month)
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return paginate(filtered_orders, page, page_size)


@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts(response: Response):
    """Get demand forecasts"""
    response.headers["Cache-Control"] = "public, max-age=300"
    return demand_forecasts


@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Pre-build set for O(1) lookups instead of O(n*m)
    po_backlog_ids = {po["backlog_item_id"] for po in purchase_orders}
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        item_dict["has_purchase_order"] = item["id"] in po_backlog_ids
        result.append(item_dict)
    return result


@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    validate_filter_param("warehouse", warehouse, WAREHOUSES)
    validate_filter_param("category", category, CATEGORIES)
    validate_filter_param("status", status, ORDER_STATUSES)
    validate_month_param(month)

    filtered_inventory = apply_filters(inventory_items, warehouse, category)
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in PENDING_STATUSES])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }


@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary


@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending


@app.get("/api/spending/categories")
def get_category_spending(response: Response):
    """Get spending by category"""
    response.headers["Cache-Control"] = "public, max-age=300"
    return category_spending


@app.get("/api/spending/transactions")
def get_recent_transactions(
    page: Optional[int] = None,
    page_size: Optional[int] = None
):
    """Get recent transactions with optional pagination"""
    return paginate(recent_transactions, page, page_size)


@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        quarter = MONTH_TO_QUARTER.get(order_date[:7])
        if not quarter:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    result.sort(key=lambda x: x['quarter'])
    return result


@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        month = order_date[:7]

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result


# --- Tasks endpoints ---
tasks_store = []


@app.get("/api/tasks")
def get_tasks():
    """Get all tasks"""
    return tasks_store


@app.post("/api/tasks")
def create_task(task: dict):
    """Create a new task"""
    task_id = uuid.uuid4().hex[:8]
    new_task = {
        "id": task_id,
        "title": task.get("title", ""),
        "status": task.get("status", "pending"),
        "created_date": datetime.now().isoformat()
    }
    tasks_store.append(new_task)
    return new_task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task"""
    global tasks_store
    tasks_store = [t for t in tasks_store if t["id"] != task_id]
    return {"status": "deleted"}


@app.patch("/api/tasks/{task_id}")
def toggle_task(task_id: str):
    """Toggle a task's status"""
    task = next((t for t in tasks_store if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task


# --- Purchase Order endpoints ---
@app.post("/api/purchase-orders")
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item"""
    po_id = uuid.uuid4().hex[:8]
    po = {
        "id": po_id,
        "backlog_item_id": request.backlog_item_id,
        "supplier_name": request.supplier_name,
        "quantity": request.quantity,
        "unit_cost": request.unit_cost,
        "total_cost": round(request.quantity * request.unit_cost, 2),
        "expected_delivery_date": request.expected_delivery_date,
        "status": "Pending",
        "created_date": datetime.now().isoformat(),
        "notes": request.notes
    }
    purchase_orders.append(po)
    logger.info("Purchase order created: %s for backlog item %s", po_id, request.backlog_item_id)
    return po


@app.get("/api/purchase-orders/{backlog_item_id}")
def get_purchase_order(backlog_item_id: str):
    """Get purchase order by backlog item ID"""
    po = next((p for p in purchase_orders if p["backlog_item_id"] == backlog_item_id), None)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


@app.get("/api/restocking/recommendations", response_model=RestockingRecommendation)
def get_restocking_recommendations(budget: float):
    """Get restocking recommendations based on budget, prioritized by demand gap"""
    if budget <= 0:
        raise HTTPException(status_code=400, detail="Budget must be a positive number")

    items = []
    for forecast in demand_forecasts:
        demand_gap = forecast["forecasted_demand"] - forecast["current_demand"]
        if demand_gap <= 0:
            continue
        unit_cost = forecast["unit_cost"]
        restock_cost = round(demand_gap * unit_cost, 2)
        items.append({
            "item_sku": forecast["item_sku"],
            "item_name": forecast["item_name"],
            "current_demand": forecast["current_demand"],
            "forecasted_demand": forecast["forecasted_demand"],
            "demand_gap": demand_gap,
            "unit_cost": unit_cost,
            "restock_cost": restock_cost,
            "included": False
        })

    # Sort by demand gap descending (highest priority first)
    items.sort(key=lambda x: x["demand_gap"], reverse=True)

    # Greedy budget allocation
    running_total = 0.0
    items_included = 0
    for item in items:
        if running_total + item["restock_cost"] <= budget:
            item["included"] = True
            running_total += item["restock_cost"]
            items_included += 1

    return {
        "items": items,
        "total_cost": round(running_total, 2),
        "budget": budget,
        "items_included": items_included
    }


@app.post("/api/restocking/orders")
def create_restocking_order(request: CreateRestockingOrderRequest):
    """Create a restocking order from recommendations"""
    order_id = uuid.uuid4().hex[:12]
    order_number = f"RST-{datetime.now().strftime('%Y')}-{order_id[:6].upper()}"
    now = datetime.now()
    order_date = now.strftime("%Y-%m-%dT%H:%M:%S")
    expected_delivery = (now + timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%S")
    total_value = round(sum(item["quantity"] * item["unit_price"] for item in request.items), 2)

    restocking_order = {
        "id": order_id,
        "order_number": order_number,
        "customer": "Restocking Order",
        "items": request.items,
        "status": "Processing",
        "order_date": order_date,
        "expected_delivery": expected_delivery,
        "total_value": total_value,
        "actual_delivery": None,
        "warehouse": None,
        "category": None,
        "order_type": "restocking"
    }

    restocking_orders.append(restocking_order)
    orders.append(restocking_order)

    logger.info("Restocking order created: %s (total: $%.2f)", order_number, total_value)
    return restocking_order


@app.get("/api/restocking/orders")
def get_restocking_orders():
    """Get all submitted restocking orders"""
    return restocking_orders


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on %s:%d", API_HOST, API_PORT)
    uvicorn.run(app, host=API_HOST, port=API_PORT)
