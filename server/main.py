from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
from typing import Literal
import itertools
import re
import threading
from pydantic import BaseModel, Field
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, tasks as seed_tasks

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    unit_cost: float
    lead_time_days: int
    current_stock: int

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_cost: float = Field(gt=0)
    expected_delivery_date: str  # YYYY-MM-DD, validated in the endpoint
    notes: Optional[str] = None

# Field names are camelCase (dueDate) on purpose: the frontend's existing task shape
# (see useAuth.js mock tasks and TasksModal.vue) uses `dueDate`, so the API matches it.
class Task(BaseModel):
    id: str
    title: str
    priority: Literal['high', 'medium', 'low']
    dueDate: str
    status: Literal['pending', 'completed'] = 'pending'

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1)
    priority: Literal['high', 'medium', 'low'] = 'medium'
    dueDate: str  # YYYY-MM-DD, validated in the endpoint

class RestockLine(BaseModel):
    sku: str
    quantity: int

class RestockOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    line_cost: float
    lead_time_days: int

class CreateRestockOrderRequest(BaseModel):
    budget: float
    items: List[RestockLine]

class RestockOrder(BaseModel):
    id: str
    order_number: str
    status: str
    budget: float
    items: List[RestockOrderItem]
    total_cost: float
    lead_time_days: int
    submitted_date: str
    estimated_delivery: str

# In-memory store for submitted restocking orders (reset on server restart, like all data here)
restock_orders: List[dict] = []

# In-memory task store, seeded from data/tasks.json (copies, so the loaded data is never mutated).
# Ids are "task-N" strings so they can never collide with the integer ids of the frontend's mock tasks.
tasks_store: List[dict] = [dict(t) for t in seed_tasks]
_task_ids = itertools.count(len(tasks_store) + 1)
_purchase_order_lock = threading.Lock()

def parse_iso_date(value: str, field_name: str) -> None:
    """Raise a 400 if value is not a valid, zero-padded YYYY-MM-DD date."""
    try:
        # strptime alone also accepts unpadded values like "2025-1-5", which browsers parse
        # inconsistently in `new Date(...)`; the regex enforces the documented ISO shape.
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError(value)
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{field_name} must be a valid date in YYYY-MM-DD format")

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/restock/recommendations")
def get_restock_recommendations(budget: float = 0):
    """Recommend forecast items to restock within a budget.

    Items are ranked by forecast growth (forecasted vs current demand). Each item's
    shortfall is forecasted_demand - current_stock; items with no shortfall are skipped.
    We fill greedily in rank order, capping quantity at what the remaining budget affords.
    """
    if budget < 0:
        raise HTTPException(status_code=422, detail="Budget must not be negative")

    candidates = []
    for f in demand_forecasts:
        shortfall = f["forecasted_demand"] - f["current_stock"]
        if shortfall > 0:
            growth = (f["forecasted_demand"] - f["current_demand"]) / f["current_demand"]
            candidates.append((growth, shortfall, f))
    # Highest growth first; larger shortfall breaks ties
    candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)

    remaining = budget
    items = []
    for growth, shortfall, f in candidates:
        # int() guards against float error when budget divides evenly by unit cost
        affordable = int((remaining + 1e-9) // f["unit_cost"])
        quantity = min(shortfall, affordable)
        if quantity <= 0:
            continue
        line_cost = round(quantity * f["unit_cost"], 2)
        remaining -= line_cost
        items.append({
            "sku": f["item_sku"],
            "name": f["item_name"],
            "quantity": quantity,
            "max_quantity": shortfall,
            "unit_cost": f["unit_cost"],
            "line_cost": line_cost,
            "lead_time_days": f["lead_time_days"],
            "growth_percent": round(growth * 100, 1),
            "trend": f["trend"],
        })

    total_cost = round(sum(i["line_cost"] for i in items), 2)
    return {
        "budget": budget,
        "items": items,
        "total_cost": total_cost,
        "remaining_budget": round(budget - total_cost, 2),
    }

@app.post("/api/restock-orders", response_model=RestockOrder)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restocking order. Lead time is the longest lead time of any line."""
    if not request.items:
        raise HTTPException(status_code=422, detail="Order must contain at least one item")

    by_sku = {f["item_sku"]: f for f in demand_forecasts}
    lines = []
    for line in request.items:
        forecast = by_sku.get(line.sku)
        if not forecast:
            raise HTTPException(status_code=404, detail=f"Unknown SKU: {line.sku}")
        if line.quantity <= 0:
            raise HTTPException(status_code=422, detail=f"Quantity must be positive for {line.sku}")
        lines.append({
            "sku": line.sku,
            "name": forecast["item_name"],
            "quantity": line.quantity,
            "unit_cost": forecast["unit_cost"],
            "line_cost": round(line.quantity * forecast["unit_cost"], 2),
            "lead_time_days": forecast["lead_time_days"],
        })

    total_cost = round(sum(l["line_cost"] for l in lines), 2)
    if total_cost > request.budget:
        raise HTTPException(status_code=422, detail="Order total exceeds budget")

    lead_time = max(l["lead_time_days"] for l in lines)
    now = datetime.now()
    number = len(restock_orders) + 1
    order = {
        "id": f"RST-{number:04d}",
        "order_number": f"RST-{number:04d}",
        "status": "Submitted",
        "budget": request.budget,
        "items": lines,
        "total_cost": total_cost,
        "lead_time_days": lead_time,
        "submitted_date": now.isoformat(timespec="seconds"),
        "estimated_delivery": (now + timedelta(days=lead_time)).isoformat(timespec="seconds"),
    }
    restock_orders.append(order)
    return order

@app.get("/api/restock-orders", response_model=List[RestockOrder])
def get_restock_orders():
    """Get submitted restocking orders, newest first"""
    return list(reversed(restock_orders))

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item (one PO per backlog item)"""
    if not request.supplier_name.strip():
        raise HTTPException(status_code=400, detail="supplier_name must not be blank")
    parse_iso_date(request.expected_delivery_date, "expected_delivery_date")

    if not any(b["id"] == request.backlog_item_id for b in backlog_items):
        raise HTTPException(status_code=404, detail=f"Backlog item {request.backlog_item_id} not found")
    now = datetime.now()
    # Sync endpoints run in a threadpool, so the duplicate check, id assignment and append must be
    # one atomic step; otherwise two concurrent requests could both pass the check (two POs for one
    # backlog item) or compute the same id from len(purchase_orders).
    with _purchase_order_lock:
        if any(po["backlog_item_id"] == request.backlog_item_id for po in purchase_orders):
            raise HTTPException(status_code=409, detail=f"Backlog item {request.backlog_item_id} already has a purchase order")

        po = {
            "id": f"PO-{now.year}-{len(purchase_orders) + 1:04d}",
            "backlog_item_id": request.backlog_item_id,
            "supplier_name": request.supplier_name.strip(),
            "quantity": request.quantity,
            "unit_cost": request.unit_cost,
            "expected_delivery_date": request.expected_delivery_date,
            "status": "Pending",
            "created_date": now.strftime("%Y-%m-%d"),
            "notes": request.notes,
        }
        # Deliberately appended to the shared list: get_backlog() derives has_purchase_order from it,
        # so the new PO shows up there immediately. Like all data here it resets on server restart.
        purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order attached to a backlog item"""
    for po in purchase_orders:
        if po["backlog_item_id"] == backlog_item_id:
            return po
    raise HTTPException(status_code=404, detail=f"No purchase order found for backlog item {backlog_item_id}")

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get tasks, newest first"""
    return list(reversed(tasks_store))

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a task"""
    title = request.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title must not be blank")
    parse_iso_date(request.dueDate, "dueDate")

    task = {
        "id": f"task-{next(_task_ids)}",
        "title": title,
        "priority": request.priority,
        "dueDate": request.dueDate,
        "status": "pending",
    }
    tasks_store.append(task)
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed"""
    for task in tasks_store:
        if task["id"] == task_id:
            task["status"] = "completed" if task["status"] == "pending" else "pending"
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task"""
    for index, task in enumerate(tasks_store):
        if task["id"] == task_id:
            tasks_store.pop(index)
            return {"message": f"Task {task_id} deleted"}
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
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
def get_category_spending():
    """Get spending by category"""
    # `percentage` is derived from `amount` (share of the category total) rather than trusting
    # the stored value: the hand-written percentages used to sum to ~124%, which made the
    # "% of total" labels on the Finance page impossible. Work on copies, never mutate loaded data.
    total = sum(c["amount"] for c in category_spending)
    result = []
    for c in category_spending:
        item = dict(c)
        item["percentage"] = round(item["amount"] / total * 100, 1) if total else 0.0
        result.append(item)
    return result

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
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

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
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

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

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

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
