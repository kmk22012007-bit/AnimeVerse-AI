from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class AnimeversePagination(PageNumberPagination):
    """
    SRS-compliant pagination:
    Uses page and page_size (default 20, max 50).
    Returns response envelope:
    {
        "results": [...],
        "pagination": {
            "page": current_page,
            "total_pages": total_pages,
            "total": total_items
        }
    }
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response({
            'results': data,
            'pagination': {
                'page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
                'total': self.page.paginator.count
            }
        })
