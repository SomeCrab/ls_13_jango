from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.viewsets import ModelViewSet
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
    CategoryCreateSerializer,
    CategoryListSerializer
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
    


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()

    def get_queryset(self):
        if self.action in ['restore', 'hard_delete']:
            return Category.objects.only_deleted()
        elif self.action == 'statistic':
            return Category.objects.include_deleted()
        return Category.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CategoryCreateSerializer
        return CategoryListSerializer

    def destroy(self, request, *args, **kwargs):
        """ Soft delete. """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # TODO: methods for action's decorators RESTful
    @action(detail=True, methods=['get'])
    def restore(self, request, pk=None):
        """ Restore soft-deleted. """
        category = self.get_object()
        if not category.is_deleted:
            return Response(
                {"error": "Category is not deleted."},
                status=status.HTTP_400_BAD_REQUEST
                )
        category.is_deleted = False
        category.deleted_at = None
        category.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def hard_delete(self, request, pk=None):
        """ Permanently delete a category. """
        category = self.get_object()
        
        if not category.is_deleted:
            return Response(
                {"error": "Only soft-deleted items can be hard deleted"},
                status=status.HTTP_400_BAD_REQUEST
                )
        
        category.hard_delete()
        return Response(
            {"status": "permanently deleted."},
            status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=False, methods=['get'])
    def statistic(self, request):
        """ Statistics for categories. """
        categories_with_tasks_count = Category.objects.annotate(tasks_count=Count('tasks'))

        data = [
            {
                "id": category.id,
                "category": category.name,
                "tasks_count": category.tasks_count
            }
            for category in categories_with_tasks_count
        ]
        return Response(data)