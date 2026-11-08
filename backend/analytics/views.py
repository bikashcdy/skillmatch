from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsAdminRole

from . import services


@api_view(["GET"])
@permission_classes([IsAdminRole])
def admin_stats(request):
    return Response(services.overview())


@api_view(["GET"])
@permission_classes([IsAdminRole])
def skill_demand_report(request):
    return Response(services.skill_demand())
