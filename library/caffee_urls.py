from django.urls import path
from . import caffee_view

urlpatterns = [
    path('apply-vendor/apply-for-vendor/cafe/', caffee_view.register_cafe, name='register_cafe'),
     path('cafe/dashboard/<str:cafe_id>/', caffee_view.cafe_dashboard, name='cafe_dashboard'),
]
