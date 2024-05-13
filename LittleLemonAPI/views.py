from django.shortcuts import render
from rest_framework import generics
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, CategorySerializer, CartSerializer, UserSerializer, CartPostSerializer, OrderSerializer

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404

from .permissions import IsDelCrew, IsManager

from datetime import date
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
    
class CartItemsView(generics.ListCreateAPIView):
    #queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.all().filter(user=self.request.user)
    
    def post(self, request):
        cart_item = CartPostSerializer(data=request.data)
        cart_item.is_valid(raise_exception=True)
        menuItemID = request.data['menuitem']
        quantity = request.data['quantity']
        menuItem = get_object_or_404(MenuItem, id=menuItemID)
        price = int(quantity) * menuItem.price
        try:
            Cart.objects.create(user=request.user, menuitem=menuItem, quantity=quantity, unit_price=menuItem.price, price=price)
            return Response("Added to cart")
        except:
            return Response("Already in cart")
        
    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response("Deleted", 200)

class OrderView(generics.ListCreateAPIView):
    #queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if IsManager().has_permission(self.request, self):
            query = Order.objects.all()
        elif IsDelCrew().has_permission(self.request, self):
            query = Order.objects.filter(delivery_crew=self.request.user)
        else:
            query = Order.objects.filter(user=self.request.user)
        return query
    """
    def get_permissions(self):
        permission_classes = [AllowAny]
        if self.request.method == 'POST':
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    """
    def post(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user)
        if len(cart.values()) == 0:
            return Response("No items in cart")
        total = 0
        for item in cart.values():
            total += item['price']
        order = Order.objects.create(user=user, total=total, date=date.today())
        for item in cart.values():
            menuItem = get_object_or_404(MenuItem, id=item['menuitem_id'])
            orderitem = OrderItem.objects.create(
                order=order,
                menuitem=menuItem,
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                price=total
                )
            orderitem.save()
        cart.delete()
        return Response("Order Placed!", 201)

class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    #queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if IsManager().has_permission(self.request, self):
            query = Order.objects.all()
        elif IsDelCrew().has_permission(self.request, self):
            query = Order.objects.filter(delivery_crew=self.request.user)
        else:
            query = Order.objects.filter(user=self.request.user)
        return query
    
    def get_permissions(self):
        permission_classes = []
        if self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        elif self.request.method == 'PATCH':
            permission_classes = [IsAuthenticated, IsManager | IsDelCrew]
        elif self.request.method == "DELETE" or self.request.method == 'PUT':
            permission_classes = [IsManager]
        return [permission() for permission in permission_classes]
    
    def patch(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        print(order.delivery_crew)
        if order.delivery_crew != self.request.user:
            return Response("Not Assigned to this order")
        order.status = not order.status
        order.save()
        return Response("Status for order #: " + str(order.id) + " changed to: " + str(order.status), 201)

    def delete(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        order.delete()
        return Response("Deleted Order", 200)

    def put(self, request, *args, **kwargs):
        order_pk = self.kwargs['pk']
        crew_pk = request.data['delivery_crew'] 
        order = get_object_or_404(Order, pk=order_pk)
        crew = get_object_or_404(User, pk=crew_pk)
        order.delivery_crew = crew
        order.save()
        return Response("Updated Delivery Crew to: " + crew.username, 201)


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
