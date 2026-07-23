from rest_framework import serializers
from .models import BatchJob, BatchFile


class BatchFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchFile
        fields = ['id', 'original_name', 'status', 'error_message', 'created_at']
        read_only_fields = fields


class BatchJobSerializer(serializers.ModelSerializer):
    files = BatchFileSerializer(many=True, read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = BatchJob
        fields = [
            'id', 'name', 'status', 'total_files', 'completed_files',
            'failed_files', 'progress_percent', 'output_zip',
            'source_language', 'target_language', 'style_mode',
            'bilingual', 'files', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'total_files', 'completed_files',
            'failed_files', 'progress_percent', 'output_zip',
            'created_at', 'updated_at',
        ]


class BatchCreateSerializer(serializers.Serializer):
    zip_file = serializers.FileField()
    name = serializers.CharField(max_length=255, required=False, default='')
    source_language = serializers.CharField(max_length=20, default='auto')
    target_language = serializers.CharField(max_length=20, default='en')
    style_mode = serializers.CharField(max_length=20, default='fluid')
    bilingual = serializers.BooleanField(default=False)
