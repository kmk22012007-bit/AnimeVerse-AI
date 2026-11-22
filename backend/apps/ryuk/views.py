from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.ryuk.models import AIConversation, AIMessage
from apps.ryuk.services import RyukService
from apps.ryuk.recommendation_service import RyukRecommendationEngine
from apps.ryuk.serializers import RyukMessageSerializer, RyukRecommendationQuerySerializer
from apps.core.pagination import AnimeversePagination
from apps.core.exceptions import ValidationError as CustomValidationError, NotFoundError
from apps.core.throttling import RyukMessageThrottle, RyukRecommendationThrottle

class RyukMessageView(APIView):
    """
    POST /api/ryuk/messages/
    Processes chat with RYUK. Returns 201 on reply, or 503 on fallback with Discovery suggestions.
    """
    throttle_classes = [RyukMessageThrottle]
    def post(self, request):
        serializer = RyukMessageSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError("Message validation failed.", details=serializer.errors)

        user = request.animeverse_user
        validated = serializer.validated_data

        service = RyukService()
        result = service.process_message(
            user=user,
            message=validated['message'],
            conversation_id=validated.get('conversation_id'),
            anime_mal_id=validated.get('anime_mal_id')
        )

        if result.get('is_fallback', False):
            return Response({
                'error': 'ai_unavailable',
                'message': 'RYUK is unavailable right now.',
                'is_fallback': True,
                'suggestions': result.get('suggestions', []),
                'conversation_id': result.get('conversation_id')
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({
            'conversation_id': result['conversation_id'],
            'reply': result['reply'],
            'is_fallback': False
        }, status=status.HTTP_201_CREATED)


class RyukConversationListView(APIView):
    """
    GET /api/ryuk/conversations/
    Lists conversations for authenticated user.
    """
    def get(self, request):
        user = request.animeverse_user
        convos = AIConversation.objects.filter(user=user).order_by('-updated_at')

        paginator = AnimeversePagination()
        page_slice = paginator.paginate_queryset(convos, request)
        results = [
            {
                'id': c.id,
                'title': c.title,
                'updated_at': c.updated_at.isoformat()
            }
            for c in page_slice
        ]
        return paginator.get_paginated_response(results)


class RyukConversationDetailView(APIView):
    """
    DELETE /api/ryuk/conversations/{id}/
    Safely deletes a conversation owned by the authenticated user.
    """
    def delete(self, request, id):
        user = request.animeverse_user
        convo = AIConversation.objects.filter(id=id, user=user).first()
        if not convo:
            raise NotFoundError("Conversation not found or access denied.")

        convo.delete()
        return Response({'message': 'Conversation deleted successfully.'}, status=status.HTTP_200_OK)


class RyukConversationClearView(APIView):
    """
    POST /api/ryuk/conversations/clear/
    Clears all conversations for the authenticated user.
    """
    def post(self, request):
        user = request.animeverse_user
        count, _ = AIConversation.objects.filter(user=user).delete()
        return Response({'message': f'Cleared {count} conversations successfully.'}, status=status.HTTP_200_OK)


class RyukConversationMessagesView(APIView):
    """
    GET /api/ryuk/conversations/{id}/messages/
    Retrieves message history for a conversation owned by the authenticated user.
    """
    def get(self, request, id):
        user = request.animeverse_user
        convo = AIConversation.objects.filter(id=id, user=user).first()
        if not convo:
            raise NotFoundError("Conversation not found.")

        messages_qs = convo.messages.order_by('created_at')
        paginator = AnimeversePagination()
        page_slice = paginator.paginate_queryset(messages_qs, request)
        results = [
            {
                'id': m.id,
                'role': m.role,
                'content': m.content,
                'is_fallback': m.is_fallback,
                'created_at': m.created_at.isoformat()
            }
            for m in page_slice
        ]
        return paginator.get_paginated_response(results)


class RyukRecommendationView(APIView):
    """
    GET /api/ryuk/recommendations/
    Personalized anime recommendations based on the user's completed,
    watching, ratings, and genre preferences. Supports mode='personalized' or 'different'.
    """
    throttle_classes = [RyukRecommendationThrottle]
    def get(self, request):
        serializer = RyukRecommendationQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            raise CustomValidationError("Recommendation query validation failed.", details=serializer.errors)

        user = request.animeverse_user
        validated = serializer.validated_data

        engine = RyukRecommendationEngine()
        data = engine.get_recommendations(
            user=user,
            requested_genre=validated.get('genre'),
            mode=validated.get('mode', 'personalized'),
            limit=validated.get('limit', 6),
            refresh=validated.get('refresh', False)
        )
        return Response(data, status=status.HTTP_200_OK)
