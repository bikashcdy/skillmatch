from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsCandidate

from .services import profile_summary, update_preferences


@api_view(["GET", "PATCH"])
@permission_classes([IsCandidate])
def profile(request):
    """The candidate's profile: preferences plus the skills, experience and education they confirmed."""
    if request.method == "PATCH":
        errors = update_preferences(request.user, request.data)
        if errors:
            return Response(errors, status=400)
    return Response(profile_summary(request.user))
