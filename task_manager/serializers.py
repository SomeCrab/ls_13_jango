from datetime import timedelta
from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password as default_validate_password
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
            'owner',
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
        read_only_fields = ['updated_at', 'created_at', 'id', 'owner']
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
        read_only_fields = ['created_at', 'owner']


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
            'owner',
            'title',
            'description',
            'category',
            'status',
            'deadline',
            'created_at',
            'updated_at',
            ]


class TaskUserListSerializer(TaskListSerializer):
    """ Tasks created by users serializer """


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
        read_only_fields = ['owner']

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
        read_only_fields = ['created_at', 'owner']


class TaskStatisticsSerializer(serializers.Serializer):
    """ Task statistics serializer. """
    total_tasks = serializers.IntegerField()
    failed_deadline_count = serializers.IntegerField()
    count_by_status = serializers.DictField()


class UserRegisterSerializer(serializers.ModelSerializer):
    # Делаем поле пароля только для записи (его нельзя будет прочитать из API)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'password', 'email']

    def create(self, validated_data):
        # Используем create_user, чтобы пароль был правильно захеширован
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )
        return user
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(f"Username {value} is taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("You cant register multiple accounts on same email.")
        return value

    def validate_password(self, value):
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one upper character.")
        
        default_validate_password(value)

        return value