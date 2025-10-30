from rest_framework import serializers
from masters.models import ModuleUE, Chapter, Lesson

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "title", "external_url", "video_file", "resource_file", "is_published", "order", "chapter"]

class ChapterSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    class Meta:
        model = Chapter
        fields = ["id", "title", "order", "lessons"]

class ModuleSerializer(serializers.ModelSerializer):
    chapters = ChapterSerializer(many=True, read_only=True)
    class Meta:
        model = ModuleUE
        fields = ["id", "title", "code", "chapters"]
