from django.urls import path

from . import views

urlpatterns = [
    path("resume/", views.upload_resume),
    path("resume/manual/", views.manual_resume),
    path("resume/ocr/", views.ocr_state),
    path("resumes/", views.my_resumes),
    path("resumes/<int:resume_id>/", views.delete_resume),
    path("resumes/<int:resume_id>/confirm/", views.confirm_resume),
    path("resumes/<int:resume_id>/file/", views.resume_file),
]
