from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import status, filters
from django_filters.rest_framework import DjangoFilterBackend
from .filters import TaskFilter
from .models import (
    Task,
    SubTask,
    Category,
    STATUS_CHOICES
    )
from .serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskStatisticsSerializer,
    SubTaskSerializer,
    SubTaskDetailsSerializer,
    SubTaskCreateSerializer,
    SubTaskUpdateSerializer,
    CategoryCreateSerializer
    )

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 2


class TaskListCreateView(ListCreateAPIView):
    """ Task list and creating view """
    queryset = Task.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    #filterset_fields = ['status', 'deadline']
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaskCreateSerializer
        return TaskListSerializer


class TaskDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return TaskUpdateSerializer
        return TaskDetailSerializer


@api_view(['GET'])
def task_statistics(request):
    """ Task statistics view """
    now = timezone.now()
    stats_kwargs = {
        'total_tasks': Count('id'),
        'failed_deadline_count': Count(
            'id',
            filter=Q(deadline__lt=now) & ~Q(status='DONE')
        ),
    }

    for status_key in STATUS_CHOICES:
        stats_kwargs[f"{status_key.lower()}_count"] = Count(
            'id',
            filter=Q(status=status_key)
        )

    statistics = Task.objects.aggregate(**stats_kwargs)

    count_by_status = {
        status_key: statistics.pop(f"{status_key.lower()}_count")
        for status_key in STATUS_CHOICES
    }

    statistics['count_by_status'] = count_by_status
    serializer = TaskStatisticsSerializer(data=statistics)
    serializer.is_valid(raise_exception=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


class SubTaskListCreateView(ListCreateAPIView):
    """ Subtasks listing and creating view. """
    queryset = SubTask.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'deadline']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SubTaskCreateSerializer
        return SubTaskSerializer


class SubTaskDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    """ View for updating, deleting or getting details of subtask. """
    queryset = SubTask.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return SubTaskUpdateSerializer
        return SubTaskDetailsSerializer