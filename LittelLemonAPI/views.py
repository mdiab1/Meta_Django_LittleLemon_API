from django.shortcuts import render
from rest_framework import generics
from .models import Category, MenuItem, Cart
from .serializers import MenuItemSerializer, CategorySerializer, CartSerializer, UserSerializer

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404

from .permissions import IsDelCrew, IsManager
# Create your views here.

class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price']
    filterset_fields = ['price', 'category']
    search_fields = ['title']
    
    def get_permissions(self):
        permission_classes = [AllowAny]
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            permission_classes = [IsAuthenticated, IsManager]
        return [permission() for permission in permission_classes]

    def put(self, request):
        return Response("Not Supported")
    
    def patch(self, request):
        return Response("Not Supported")
    
    def delete(self, request):
        return Response("Not Supported")
    
class MenuItemSingleView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    
    def get_permissions(self):
        permission_classes = [AllowAny]
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            permission_classes = [IsAuthenticated, IsManager]
        return [permission() for permission in permission_classes]
    

    
    



@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def managers(request):
    username = request.user
    user_in_group = username.groups.filter(name="Managers").exists()
    if username and user_in_group:
        managers = Group.objects.get(name="Managers")
        if request.method == 'GET':
            return Response(UserSerializer(managers.user_set.all(), many=True).data)
        elif request.method == 'POST':
            user_to_add = request.data['username']
            user = User.objects.get(username=user_to_add)
            managers.user_set.add(user)
            return Response(status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            print(request.data)
            user_to_remove = request.data['username']
            user = User.objects.get(username=user_to_remove)
            user_in_group = user.groups.filter(name="Managers").exists()
            if user_in_group:
                managers.user_set.remove(user)
                return Response(status.HTTP_200_OK)
            else:
                return Response(status.HTTP_404_NOT_FOUND)
    return Response()

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def delivery_crew(request):
    username = request.user
    is_user_in_managers_group = username.groups.filter(name="Managers").exists()
    if username and is_user_in_managers_group:
        delivery_crew_users = Group.objects.get(name="Delivery_Crew")
        if request.method == 'GET':
            return Response(UserSerializer(delivery_crew_users.user_set.all(), many=True).data)
        elif request.method == 'POST':
            user_to_add = request.data['username']
            user = User.objects.get(username=user_to_add)
            delivery_crew_users.user_set.add(user)
            return Response(status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            print(request.data)
            user_to_remove = request.data['username']
            user = User.objects.get(username=user_to_remove)
            user_in_group = user.groups.filter(name="Delivery_Crew").exists()
            if user_in_group:
                delivery_crew_users.user_set.remove(user)
                return Response(status.HTTP_200_OK)
            else:
                return Response(status.HTTP_404_NOT_FOUND)
    return Response()
