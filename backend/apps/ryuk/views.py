from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.ryuk.models import AIConversation, AIMessage
from apps.ryuk.services import RyukService
from apps.ryuk.serializers import RyukMessageSerializer
from apps.core.pagination import AnimeversePagination
from apps.core.exceptions import ValidationError as CustomValidationError, NotFoundError

class RyukMessageView(APIView):
    """
    SRS POST /api/ryuk/messages/
    Processes chat with RYUK. Returns 201 on reply, or 503 on fallback with Discovery suggestions.
    """
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
            # SRS Page 32, 33: Returns 503 with fallback message and suggestions
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
    SRS GET /api/ryuk/conversations/
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

class RyukConversationMessagesView(APIView):
    """
    SRS GET /api/ryuk/conversations/{id}/messages/
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
