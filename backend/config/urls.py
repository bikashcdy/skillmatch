from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def home(request):
    return HttpResponse(
        "<body style='font-family:sans-serif;max-width:560px;margin:60px auto;line-height:1.6'>"
        "<h2>JobMitra API is running ✅</h2>"
        "<p>This is the backend. Open the app at "
        "<a href='http://localhost:5173'>http://localhost:5173</a>.</p>"
        "<p><a href='/admin/'>Admin panel</a></p></body>"
    )


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
]  # resume files are private: served only by /api/resumes/<id>/file/ after a permission check
