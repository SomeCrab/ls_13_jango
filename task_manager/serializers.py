from rest_framework import serializers
from .models import Task


class TaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'category',
            'status',
            'deadline',
            'created_at',
            'updated_at'
            ]


class TaskDetailSerializer(TaskListSerializer):
    pass


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'category',
            'status',
            'deadline'
            ]
        

class TaskStatisticsSerializer(serializers.Serializer):
    total_tasks = serializers.IntegerField()
    failed_deadline_count = serializers.IntegerField()
    count_by_status = serializers.DictField()
