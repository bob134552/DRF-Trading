from django.http import Http404
from oauth2_provider.contrib.rest_framework import (OAuth2Authentication,
                                                    TokenHasReadWriteScope,)
from rest_framework import generics, permissions, viewsets, mixins
from rest_framework.exceptions import PermissionDenied
from api_user.serializers import UserSerializer, AllUsersSerializer

from django.contrib.auth.models import User