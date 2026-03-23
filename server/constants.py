"""Constants for the Factory Inventory Management System"""

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

# Valid order statuses
ORDER_STATUSES = {"Delivered", "Shipped", "Processing", "Backordered"}

# Pending statuses (not yet fulfilled)
PENDING_STATUSES = {"Processing", "Backordered"}

# Valid categories
CATEGORIES = {"Circuit Boards", "Sensors", "Actuators", "Controllers", "Power Supplies"}

# Valid warehouses
WAREHOUSES = {"San Francisco", "London", "Tokyo"}

# Valid month formats (YYYY-MM)
VALID_MONTHS = {f"2025-{m:02d}" for m in range(1, 13)}

# Reverse lookup: YYYY-MM -> quarter name (O(1) per order)
MONTH_TO_QUARTER = {m: q for q, months in QUARTER_MAP.items() for m in months}
