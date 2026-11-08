from django.urls import path

from . import views

urlpatterns = [
    path("jobs/<int:job_id>/apply/", views.ApplyView.as_view()),
    path("my-applications/", views.MyApplicationsView.as_view()),
    path("my-applications/<int:app_id>/", views.withdraw_application),
    path("recruiter/jobs/<int:job_id>/candidates/", views.ranked_candidates),
    path("recruiter/jobs/<int:job_id>/select-best/", views.auto_select),
    path("recruiter/applications/<int:app_id>/note/", views.set_note),
    path("recruiter/applications/<int:app_id>/status/", views.set_status),
]
