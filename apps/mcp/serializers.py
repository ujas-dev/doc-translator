from rest_framework import serializers


class MCPTranslateSerializer(serializers.Serializer):
    text = serializers.CharField()
    source_lang = serializers.CharField(max_length=10, default='auto')
    target_lang = serializers.CharField(max_length=10, default='en')
    style = serializers.ChoiceField(
        choices=['faithful', 'fluid', 'creative', 'formal', 'casual'],
        default='fluid',
    )


class MCPTranslateDocSerializer(serializers.Serializer):
    file = serializers.FileField()
    target_lang = serializers.CharField(max_length=10, default='en')
    style = serializers.ChoiceField(
        choices=['faithful', 'fluid', 'creative', 'formal', 'casual'],
        default='fluid',
    )


class MCPGlossarySerializer(serializers.Serializer):
    glossary_id = serializers.IntegerField()
    text = serializers.CharField()


class MCPTMSearchSerializer(serializers.Serializer):
    source_text = serializers.CharField()
    source_lang = serializers.CharField(max_length=10, default='en')
    target_lang = serializers.CharField(max_length=10, default='hi')
