from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
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
    TaskStatisticsSerializer,
    SubTaskSerializer,
    SubTaskDetailsSerializer,
    SubTaskCreateSerializer,
    SubTaskUpdateSerializer,
    CategoryCreateSerializer
    )

# TODO: classify remain views
@api_view(['GET'])
def task_list(request):
    """ Multiple tasks view """
    filters = {}
    deadline = request.query_params.get('deadline')
    if deadline:
        filters['deadline__week_day'] = deadline
    tasks = Task.objects.filter(**filters)
    serializer = TaskListSerializer(tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def task_detail(request, pk):
    """ Single task detailed view """
    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'},
                        status=status.HTTP_404_NOT_FOUND
                        )
    serializer = TaskDetailSerializer(task)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def task_create(request):
    """ Task creating view """
    serializer = TaskCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED
                        )
    else:
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST
                        )


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


class SubTaskListCreateView(APIView, PageNumberPagination):
    """ Subtasks listing and creating view. """
    page_size = 5

    def get(self, request):
        filter_params = ['task', 'status']
        filters = {param: request.query_params.get(param) for param in filter_params if request.query_params.get(param) is not None}

        subtasks = SubTask.objects.filter(**filters) if filters else SubTask.objects.all()
        if not subtasks.exists():
            return Response({"detail": "No subtasks yet."}, status=status.HTTP_200_OK)
        page_size = self.get_page_size(request)
        self.page_size = page_size

        sort_by = request.query_params.get('sort_by', '-created_at')
        sort_order = request.query_params.get('sort_order', 'desc')
        if sort_order == 'asc':
            sort_by = sort_by.replace('-', '')
        sorted_subtasks = subtasks.order_by(sort_by)

        paginated_subtasks = self.paginate_queryset(sorted_subtasks, request, view=self)
        serializer = SubTaskSerializer(paginated_subtasks, many=True)
        return self.get_paginated_response(serializer.data)
    
    def post(self, request):
        serializer = SubTaskCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_page_size(self, request):
        """ Page size method """
        page_size = request.query_params.get('page_size')
        if page_size and page_size.isdigit():
            return int(page_size)
        return self.page_size


class SubTaskDetailUpdateDeleteView(APIView):
    """ View for updating, deleting or getting details of subtask. """
    def get(self, request, pk):
        try:
            subtask = SubTask.objects.get(pk=pk)
        except SubTask.DoesNotExist:
            return Response({'error': 'Subtask not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SubTaskDetailsSerializer(subtask)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, pk):
        try:
            subtask = SubTask.objects.get(pk=pk)
        except SubTask.DoesNotExist:
            return Response({'error': 'Subtask not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SubTaskUpdateSerializer(subtask, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            subtask = SubTask.objects.get(pk=pk)
        except SubTask.DoesNotExist:
            return Response({'error': 'Subtask not found'}, status=status.HTTP_404_NOT_FOUND)
        subtask.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)