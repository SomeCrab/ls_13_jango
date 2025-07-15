from django.urls import path
from .views import (
    task_list,
    task_detail,
    task_create,
    task_statistics,
    SubTaskListCreateView,
    SubTaskDetailUpdateDeleteView
    )
# TODO: classify remain paths
urlpatterns = [
    path('tasks/', task_list, name='task-list'),
    path('tasks/<int:pk>/', task_detail, name='task-detail'),
    path('tasks/create/', task_create, name='task-create'),
    path('tasks/statistics/', task_statistics, name='statistics'),
    path('subtasks/', SubTaskListCreateView.as_view(), name='subtasks-list-create'),
    path('subtasks/<int:pk>/', SubTaskDetailUpdateDeleteView.as_view(), name='subtasks-detail-update-delete'),
    ]