from django.urls import path

from . import views

urlpatterns = [
    path("matching/jobs/<int:job_id>/", views.job_match),
    path("admin/weights/", views.admin_weights),
    path("admin/weights/tune/", views.admin_tune),
    path("admin/weights/reset/", views.admin_activate_weights),
    path("admin/weights/<int:config_id>/activate/", views.admin_activate_weights),
    path("admin/ratings/", views.admin_rate),
    path("admin/ratings/import-decisions/", views.admin_import_decisions),
    path("admin/ratings/<int:rating_id>/", views.admin_delete_rating),
]
