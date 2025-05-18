from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="User Management API",
        default_version='v1',
        description=(
            "API for managing farmers, experts, and admins in an agricultural platform. "
            "Endpoints are grouped as follows:\n"
            "- /api/auth/: User registration, password management, and token handling.\n"
            "- /api/users/: User profile management and admin user oversight.\n"
            "- /api/community/: Community posts, responses, moderation, and points system.\n"
            "- /api/consultations/: Expert availability and consultation bookings.\n"
            "- /api/crop-health/: Disease history, crop health alerts, and model retraining.\n"
            "- /api/content/: Educational content submission and approval.\n"
            "- /api/system/: System health and feedback analysis.\n"
            "- /api/crop-types/: Utility endpoint for crop type enumeration."
        ),
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="philbindya55@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)