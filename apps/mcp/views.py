import structlog
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    MCPTranslateSerializer,
    MCPTranslateDocSerializer,
    MCPGlossarySerializer,
    MCPTMSearchSerializer,
)

logger = structlog.get_logger(__name__)


class MCPBaseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        from apps.accounts.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not profile.has_feature('api_access'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('This feature requires a higher plan.')


class MCPTranslateView(MCPBaseView):

    def post(self, request):
        serializer = MCPTranslateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.translation.services import translate_text

        data = serializer.validated_data
        result = translate_text(
            data['text'],
            source=data['source_lang'],
            target=data['target_lang'],
            style=data['style'],
        )

        return Response({
            'translated': result,
            'source_lang': data['source_lang'],
            'target_lang': data['target_lang'],
            'style': data['style'],
        })


class MCPTranslateDocView(MCPBaseView):

    def post(self, request):
        serializer = MCPTranslateDocSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        from apps.documents.models import DocumentJob
        from apps.documents.tasks import process_document

        job = DocumentJob.objects.create(
            source_file=data['file'],
            target_language=data['target_lang'],
            style_mode=data['style'],
        )

        process_document.delay(job.pk)

        return Response({
            'job_id': job.pk,
            'status': job.status,
            'message': 'Document translation started',
        }, status=status.HTTP_201_CREATED)


class MCPGlossaryView(MCPBaseView):

    def get(self, request):
        serializer = MCPGlossarySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        from apps.glossaries.models import Glossary, GlossaryEntry

        data = serializer.validated_data
        try:
            glossary = Glossary.objects.get(
                pk=data['glossary_id'],
                user=request.user,
            )
        except Glossary.DoesNotExist:
            return Response(
                {'error': 'Glossary not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        entries = GlossaryEntry.objects.filter(
            glossary=glossary,
            source__icontains=data['text'],
        )

        return Response({
            'glossary': glossary.name,
            'matches': [
                {'source': e.source, 'target': e.target, 'context': e.context}
                for e in entries
            ],
        })


class MCPTMSearchView(MCPBaseView):

    def post(self, request):
        serializer = MCPTMSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.memory.models import TMEntry
        from apps.memory.services import TranslationMemoryService

        data = serializer.validated_data
        matches = TranslationMemoryService.find_matches(
            user=request.user,
            source_lang=data['source_lang'],
            target_lang=data['target_lang'],
            text=data['source_text'],
        )

        return Response({
            'source_text': data['source_text'],
            'matches': matches,
        })
