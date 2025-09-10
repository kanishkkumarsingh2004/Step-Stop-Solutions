from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('library.urls')),
    path('', include(('library.institute_urls', 'coaching'), namespace='coaching')),
    path('', include('library.gym_urls')),
    path('', include('library.caffee_urls')),

]
