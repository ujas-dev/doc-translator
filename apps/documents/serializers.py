from rest_framework import serializers
from .models import DocumentJob


class DocumentJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentJob
        fields = '__all__'
        read_only_fields = (
            'user', 'status', 'error_message', 'pages',
            'page_count', 'character_count',
            'created_at', 'updated_at', 'output_file',
        )
