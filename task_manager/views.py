from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView
    )
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework import status, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
import secrets
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
    TaskUserListSerializer,
    TaskDetailSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskStatisticsSerializer,
    SubTaskSerializer,
    SubTaskDetailsSerializer,
    SubTaskCreateSerializer,
    SubTaskUpdateSerializer,
    CategoryCreateSerializer,
    CategoryListSerializer,
    UserRegisterSerializer,
    )
from task_manager.permissions import IsOwnerOrReadOnly

def set_jwt_cookies(response, user):
    """ set JWT cookies + CSRF """
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    
    csrf_token = secrets.token_urlsafe(32)
    access_token['csrf'] = csrf_token
    
    response.set_cookie(
        key='access_token',
        value=str(access_token),
        max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite='Lax',
        path='/'
    )
    
    response.set_cookie(
        key='refresh_token',
        value=str(refresh),
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite='Lax',
        path='/'
    )
    
    return csrf_token

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            response = Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_200_OK)
            
            csrf_token = set_jwt_cookies(response, user)
            response.data['csrf_token'] = csrf_token
            
            return response
            
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

class RegistrationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            response = Response({
                'message': 'Registration successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)
            
            csrf_token = set_jwt_cookies(response, user)
            response.data['csrf_token'] = csrf_token
            
            return response
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                
        except TokenError:
            pass
        
        response = Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )
        
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        return response


class TaskListCreateView(ListCreateAPIView):
    """ Task list and creating view """
    queryset = Task.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaskCreateSerializer
        return TaskListSerializer
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TaskUserListView(ListAPIView):
    """ View for updating, deleting or getting details of task. """
    serializer_class = TaskUserListSerializer
    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)


class TaskDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOrReadOnly]
    queryset = Task.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return TaskUpdateSerializer
        return TaskDetailSerializer
    
    # def perform_update(self, serializer):
    #     instance = serializer.instance
    #     updated_fields = list(serializer.validated_data.keys())
    #     print(updated_fields)
    #     for field, value in serializer.validated_data.items():
    #         setattr(instance, field, value)
    #     instance.save(update_fields=updated_fields)



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

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SubTaskCreateSerializer
        return SubTaskSerializer
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class SubTaskDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    """ View for updating, deleting or getting details of subtask. """
    permission_classes = [IsOwnerOrReadOnly]
    queryset = SubTask.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return SubTaskUpdateSerializer
        return SubTaskDetailsSerializer
    
    def perform_update(self, serializer):
        updated_fields = list(serializer.validated_data.keys())
        
        serializer.save(update_fields=updated_fields)


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    pagination_class = None

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

    @action(detail=True, methods=['POST'])
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

    @action(detail=True, methods=['DELETE'])
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

    @action(detail=False, methods=['GET'])
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