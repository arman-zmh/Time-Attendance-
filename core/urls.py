from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import add_user_view

#router = DefaultRouter()
#router.register(r'staff', add_user_view, basename='staff') # مسیر /staff/ خواهد بود

urlpatterns = [
    path('page/', add_user_view, name='staff_page'),
]