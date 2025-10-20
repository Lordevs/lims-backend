"""
Pagination utility functions for API endpoints
"""

import math


def get_pagination_params(request):
    """
    Extract pagination parameters from request
    Returns: (page, limit, offset)
    """
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
    except (ValueError, TypeError):
        page = 1
        limit = 10
    
    # Ensure positive values
    page = max(1, page)
    limit = max(1, min(limit, 100))  # Cap at 100 items per page
    
    offset = (page - 1) * limit
    
    return page, limit, offset


def create_pagination_response(data, total_records, page, limit):
    """
    Create standardized pagination response
    """
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 1
    has_next = page < total_pages
    
    return {
        'data': data,
        'pagination': {
            'current_page': page,
            'limit': limit,
            'total_records': total_records,
            'total_pages': total_pages,
            'has_next': has_next
        }
    }


def paginate_queryset(queryset, page, limit):
    """
    Paginate a queryset and return paginated data with metadata
    """
    total_records = queryset.count()
    offset = (page - 1) * limit
    
    # Get paginated data
    paginated_data = queryset.skip(offset).limit(limit)
    
    return paginated_data, total_records


def paginate_list(data_list, page, limit):
    """
    Paginate a list and return paginated data with metadata
    """
    total_records = len(data_list)
    offset = (page - 1) * limit
    
    # Get paginated data
    paginated_data = data_list[offset:offset + limit]
    
    return paginated_data, total_records
