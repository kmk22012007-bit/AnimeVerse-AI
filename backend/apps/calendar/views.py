from rest_framework.views import APIView
from rest_framework.response import Response
from apps.anime.jikan_client import JikanClient
from apps.anime.content_filter import filter_anime_list, is_excluded_adult_anime
from apps.core.exceptions import ValidationError as CustomValidationError

class CalendarSeasonView(APIView):
    """
    SRS GET /api/calendar/season/
    Query: year (2000 to 2100), season (winter, spring, summer, fall), page
    """
    def get(self, request):
        year_str = request.query_params.get('year')
        season = request.query_params.get('season')
        page = int(request.query_params.get('page', 1))

        year = None
        if year_str:
            try:
                year = int(year_str)
                if not (2000 <= year <= 2100):
                    raise CustomValidationError("Year must be between 2000 and 2100.", details={'year': 'Invalid range.'})
            except ValueError:
                raise CustomValidationError("Year must be a valid integer.", details={'year': 'Not an integer.'})

        if season:
            season = season.lower().strip()
            if season not in ['winter', 'spring', 'summer', 'fall']:
                raise CustomValidationError(
                    "Season must be one of winter, spring, summer, fall.",
                    details={'season': 'Invalid season.'}
                )

        client = JikanClient()
        res = client.get_season_anime(year=year, season=season, page=page)
        if not res or 'data' not in res:
            return Response({'results': [], 'pagination': {'page': page, 'total_pages': 1, 'total': 0}})

        results = [client.normalize_release(item) for item in res['data'] if not is_excluded_adult_anime(item)]
        results = filter_anime_list(results)
        pagination = res.get('pagination', {})
        return Response({
            'results': results,
            'pagination': {
                'page': page,
                'total_pages': pagination.get('last_visible_page', 1),
                'total': pagination.get('items', {}).get('total', len(results))
            }
        })

class CalendarUpcomingView(APIView):
    """
    SRS GET /api/calendar/upcoming/
    """
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        client = JikanClient()
        res = client.get_upcoming_anime(page=page)
        if not res or 'data' not in res:
            return Response({'results': [], 'pagination': {'page': page, 'total_pages': 1, 'total': 0}})

        results = [client.normalize_release(item) for item in res['data'] if not is_excluded_adult_anime(item)]
        results = filter_anime_list(results)
        pagination = res.get('pagination', {})
        return Response({
            'results': results,
            'pagination': {
                'page': page,
                'total_pages': pagination.get('last_visible_page', 1),
                'total': pagination.get('items', {}).get('total', len(results))
            }
        })
