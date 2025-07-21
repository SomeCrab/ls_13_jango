from datetime import timedelta
from rest_framework import serializers
from django.utils import timezone
from .models import (
    Task,
    SubTask,
    Category
    )


class SubTaskSerializer(serializers.ModelSerializer):
    """ Sub Task model serializer. """
    class Meta:
        """ Meta class """
        model = SubTask
        fields = [
            'id',
            'title',
            'description',
            'task',
            'status',
            'deadline',
            'created_at',
            'updated_at'
            ]


class SubTaskDetailsSerializer(SubTaskSerializer):
    """ Sub Task details model serializer. """


class SubTaskCreateSerializer(SubTaskSerializer):
    """ Sub Task creation model serializer. """
    #created_at = serializers.DateTimeField(read_only=True)
    class Meta(SubTaskSerializer.Meta):
        """ Meta meta class. """
        fields = [
            'title',
            'description',
            'task',
            'status',
            'deadline'
            ]
        read_only_fields = ['updated_at', 'created_at', 'id']
        #strict = True


class SubTaskUpdateSerializer(serializers.ModelSerializer):
    """ Sub Task update model serializer. """
    class Meta:
        """ Meta class """
        model = SubTask
        fields = [
            'title',
            'description',
            'task',
            'status',
            'deadline',
            'created_at',
            ]
        read_only_fields = ['created_at']


class CategoryListSerializer(serializers.ModelSerializer):
    """ Category creation model serializer. """
    class Meta:
        model = Category
        fields = ['id', 'name']



class CategoryCreateSerializer(serializers.ModelSerializer):
    """ Category creation model serializer. """
    class Meta:
        model = Category
        fields = ['name']


    def validate_name(self, value):
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise serializers.ValidationError({"name": "Category name must be unique."})
        return value

    # def create(self, validated_data):
    #     return super().create(validated_data)

    # def update(self, instance, validated_data):
    #     return super().update(instance, validated_data)


class TaskListSerializer(serializers.ModelSerializer):
    """ Task list model serializer. """
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
    """ Task detail model serializer. """
    subtasks = SubTaskSerializer(many=True, read_only=True)
    class Meta(TaskListSerializer.Meta):
        fields = TaskListSerializer.Meta.fields + ['subtasks']

class TaskCreateSerializer(serializers.ModelSerializer):
    """ Task creation model serializer. """
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'category',
            'status',
            'deadline'
            ]

    def validate_deadline(self, value):
        if value in (None, '', 'null'):
            return value

        if value <= timezone.now() + timedelta(minutes=1):
            raise serializers.ValidationError({"deadline" : "Deadline can not be in the past."})
        return value


class TaskUpdateSerializer(serializers.ModelSerializer):
    """ Task update model serializer. """
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'category',
            'status',
            'deadline',
            'created_at'
            ]
        read_only_fields = ['created_at']


class TaskStatisticsSerializer(serializers.Serializer):
    """ Task statistics serializer. """
    total_tasks = serializers.IntegerField()
    failed_deadline_count = serializers.IntegerField()
    count_by_status = serializers.DictField()