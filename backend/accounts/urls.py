from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view()),
    path("auth/check/", views.check_availability),
    path("auth/forgot-password/", views.forgot_password),
    path("auth/reset-password/", views.reset_password),
    path("auth/change-password/", views.change_password),
    path("auth/login/", TokenObtainPairView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", views.me),
    path("admin/users/", views.AdminUserListView.as_view()),
    path("admin/users/<int:user_id>/toggle/", views.toggle_user),
    path("admin/users/<int:user_id>/approve/", views.approve_recruiter),
]
