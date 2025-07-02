from django.urls import path
from .views import (
    task_list,
    task_detail,
    task_create,
    task_statistics
    )

urlpatterns = [
    path('tasks/', task_list, name='task-list'),
    path('tasks/<int:pk>/', task_detail, name='task-detail'),
    path('tasks/create/', task_create, name='task-create'),
    path('tasks/statistics/', task_statistics, name='statistics'),
    ]