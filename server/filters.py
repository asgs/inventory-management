"""Filter and pagination utilities for the Factory Inventory Management System"""

import math
from typing import Optional
from constants import QUARTER_MAP


def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        if month in QUARTER_MAP:
            valid_months = set(QUARTER_MAP[month])
            return [item for item in items if item.get('order_date', '')[:7] in valid_months]
    else:
        return [item for item in items if item.get('order_date', '')[:7] == month]

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


def paginate(items: list, page: Optional[int] = None, page_size: Optional[int] = None) -> dict:
    """Paginate a list of items. If no page given, returns all items."""
    total = len(items)

    if page is None:
        return {
            "items": items,
            "total": total,
            "page": 1,
            "page_size": total,
            "total_pages": 1
        }

    page = max(1, page)
    page_size = max(1, min(page_size or 50, 200))
    total_pages = max(1, math.ceil(total / page_size))
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }
