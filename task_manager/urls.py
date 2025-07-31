from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskListCreateView,
    TaskUserListView,
    TaskDetailUpdateDeleteView,
    task_statistics,
    SubTaskListCreateView,
    SubTaskDetailUpdateDeleteView,
    CategoryViewSet,
    LoginView,
    RegistrationView,
    LogoutView,
    )
from django.views.decorators.csrf import csrf_exempt
from django.urls import re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


router = DefaultRouter()
router.register('categories', CategoryViewSet)

urlpatterns = [
    path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('tasks/', csrf_exempt(TaskListCreateView.as_view()), name='tasks-list-create'),
    path('user-tasks/', csrf_exempt(TaskUserListView.as_view()), name='user-tasks-list'),
    path('tasks/<int:pk>/', TaskDetailUpdateDeleteView.as_view(), name='task-detail-update-delete'),
    path('tasks/statistics/', task_statistics, name='statistics'),
    path('subtasks/', SubTaskListCreateView.as_view(), name='subtasks-list-create'),
    path('subtasks/<int:pk>/', SubTaskDetailUpdateDeleteView.as_view(), name='subtasks-detail-update-delete'),
    path('', include(router.urls)),
    path('login/', csrf_exempt(LoginView.as_view()), name='manager-login'),
    path('registration/', RegistrationView.as_view(), name='manager-registration'),
    path('logout/', LogoutView.as_view(), name='manager-logout'),
    ]