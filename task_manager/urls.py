from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskListCreateView,
    TaskDetailUpdateDeleteView,
    task_statistics,
    SubTaskListCreateView,
    SubTaskDetailUpdateDeleteView,
    CategoryViewSet
    )

router = DefaultRouter()
router.register('categories', CategoryViewSet)

urlpatterns = [
    path('tasks/', TaskListCreateView.as_view(), name='tasks-list-create'),
    path('tasks/<int:pk>/', TaskDetailUpdateDeleteView.as_view(), name='task-detail-update-delete'),
    path('tasks/statistics/', task_statistics, name='statistics'),
    path('subtasks/', SubTaskListCreateView.as_view(), name='subtasks-list-create'),
    path('subtasks/<int:pk>/', SubTaskDetailUpdateDeleteView.as_view(), name='subtasks-detail-update-delete'),
    path('', include(router.urls)),
    ]