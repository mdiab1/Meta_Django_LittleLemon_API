from django.urls import path
from . import views

urlpatterns = [
    path('menu-items', views.MenuItemsView.as_view()),
    path('menu-items/<int:pk>', views.MenuItemSingleView.as_view()),
    path('groups/manager/users', views.managers),
    path('groups/delivery-crew/users', views.delivery_crew),
    path('cart/menu-items', views.CartItemsView.as_view()),
]