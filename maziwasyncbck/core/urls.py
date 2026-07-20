# from django.urls import path
# from core import views

# urlpatterns = [
#     path('auth/register/', views.Register),
#     path('auth/login/', views.Login),
#     path('auth/me/ ',views.MyProfile),
# ]
from django.urls import path
from .views import Logout, Register, Login, MyProfile

urlpatterns = [
    path("auth/register/", Register, name="register"),
    path("auth/login/", Login, name="login"),
    path("auth/me/", MyProfile, name="my-profile"),
    path("auth/logout/", Logout, name="logout"),
]