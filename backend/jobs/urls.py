from django.urls import path

from . import views

urlpatterns = [
    path("jobs/", views.JobListView.as_view()),
    path("jobs/<int:job_id>/", views.JobDetailView.as_view()),
    path("jobs/meta/", views.job_meta),
    path("recruiter/jobs/", views.RecruiterJobView.as_view()),
    path("recruiter/jobs/<int:pk>/", views.RecruiterJobDetailView.as_view()),
    path("admin/jobs/", views.admin_jobs),
    path("admin/jobs/<int:job_id>/", views.admin_delete_job),
]
