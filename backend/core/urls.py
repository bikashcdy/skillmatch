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
    path("jobs/", views.JobListView.as_view()),
    path("jobs/<int:job_id>/", views.JobDetailView.as_view()),
    path("jobs/meta/", views.job_meta),
    path("jobs/<int:job_id>/apply/", views.ApplyView.as_view()),
    path("resume/", views.upload_resume),
    path("recommendations/", views.recommendations),
    path("my-applications/", views.MyApplicationsView.as_view()),
    path("my-applications/<int:app_id>/", views.withdraw_application),
    path("resumes/", views.my_resumes),
    path("resumes/<int:resume_id>/", views.delete_resume),
    path("resumes/<int:resume_id>/file/", views.resume_file),
    path("recruiter/jobs/", views.RecruiterJobView.as_view()),
    path("recruiter/jobs/<int:pk>/", views.RecruiterJobDetailView.as_view()),
    path("recruiter/jobs/<int:job_id>/candidates/", views.ranked_candidates),
    path("recruiter/jobs/<int:job_id>/select-best/", views.auto_select),
    path("recruiter/applications/<int:app_id>/note/", views.set_note),
    path("recruiter/applications/<int:app_id>/status/", views.set_status),
    path("admin/stats/", views.admin_stats),
    path("admin/users/", views.AdminUserListView.as_view()),
    path("admin/users/<int:user_id>/toggle/", views.toggle_user),
    path("admin/users/<int:user_id>/approve/", views.approve_recruiter),
    path("admin/jobs/", views.admin_jobs),
    path("admin/jobs/<int:job_id>/", views.admin_delete_job),
]
