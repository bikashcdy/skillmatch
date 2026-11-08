from django.urls import path

from . import views

urlpatterns = [
    path("admin/stats/", views.admin_stats),
    path("admin/analytics/skill-demand/", views.skill_demand_report),
]
