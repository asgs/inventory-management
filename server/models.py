"""Pydantic models for the Factory Inventory Management System"""

from typing import List, Optional
from pydantic import BaseModel


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
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None


class RestockingItem(BaseModel):
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    demand_gap: int
    unit_cost: float
    restock_cost: float
    included: bool


class RestockingRecommendation(BaseModel):
    items: List[RestockingItem]
    total_cost: float
    budget: float
    items_included: int


class CreateRestockingOrderRequest(BaseModel):
    items: List[dict]
    budget: float


class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int
