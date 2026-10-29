from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view()),
    path("auth/login/", TokenObtainPairView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", views.me),
    path("jobs/", views.JobListView.as_view()),
    path("jobs/<int:job_id>/save/", views.save_job),
    path("jobs/meta/", views.job_meta),
    path("jobs/<int:job_id>/apply/", views.ApplyView.as_view()),
    path("resume/", views.upload_resume),
    path("recommendations/", views.recommendations),
    path("my-applications/", views.MyApplicationsView.as_view()),
    path("recruiter/jobs/", views.RecruiterJobView.as_view()),
    path("recruiter/jobs/<int:pk>/", views.RecruiterJobDetailView.as_view()),
    path("recruiter/jobs/<int:job_id>/candidates/", views.ranked_candidates),
    path("recruiter/jobs/<int:job_id>/select-best/", views.auto_select),
    path("recruiter/applications/<int:app_id>/note/", views.set_note),
    path("recruiter/applications/<int:app_id>/status/", views.set_status),
    path("admin/stats/", views.admin_stats),
    path("admin/users/", views.AdminUserListView.as_view()),
    path("admin/users/<int:user_id>/toggle/", views.toggle_user),
]
