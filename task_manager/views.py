from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Task, STATUS_CHOICES
from .serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateSerializer,
    TaskStatisticsSerializer
    )


@api_view(['GET'])
def task_list(request):
    tasks = Task.objects.all()
    serializer = TaskListSerializer(tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def task_detail(request, pk):
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
    now = timezone.now()

    # 1 - bad, 3 requests to a db
    # total_tasks = Task.objects.aggregate(
    #         total_count=Count('id')
    #     )['total_count']
    # failed_deadline_count = Task.objects.filter(deadline__lt=now).exclude(status='DONE').count()

    # 2 - bad, 2 requests to a db
    # statistics = Task.objects.aggregate(
    #     total_tasks=Count('id'),
    #     failed_deadline_count=Count(
    #         'id',
    #         filter=Q(deadline__lt=now) & ~Q(status='DONE')
    #     )
    # )
    # count_by_status = Task.objects.values('status').annotate(count=Count('id'))
    # count_by_status_dict = {item['status']: item['count'] for item in count_by_status}

    # 1
    # statistics = {
    #     'total_tasks': total_tasks,
    #     'count_by_status': count_by_status_dict,
    #     'failed_deadline_count': failed_deadline_count,
    # }

    # 2
    # statistics['count_by_status'] = count_by_status_dict

    # 3 - good, single request to a db
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
    # end 3
    serializer = TaskStatisticsSerializer(data=statistics)
    serializer.is_valid(raise_exception=True)
    return Response(serializer.data, status=status.HTTP_200_OK)