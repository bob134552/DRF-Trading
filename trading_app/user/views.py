"""
Views for the user API
"""
from drf_spectacular.utils import extend_schema

from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
)

@extend_schema(
    summary="Create a new user",
    description="Endpoint for registering a new user in the system. \
        Requires user details like username, email, password, etc."
)
class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = UserSerializer

@extend_schema(
    summary="Obtain Auth Token",
    description="Endpoint for generating an authentication token for an existing user. \
        Requires valid email and password."
)
class CreateTokenView(ObtainAuthToken):
    """create a new auth token for user"""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

@extend_schema(
    summary="Manage authenticated user",
    description="Endpoint for retrieving and updating the authenticated user's information."
)
class ManageUserView(generics.RetrieveUpdateAPIView):
    """manage the authenticated user"""
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """retrieve and return the authenticated user"""
        return self.request.user
