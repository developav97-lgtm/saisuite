"""
SaiSuite — Users Serializers
"""
from rest_framework import serializers
from .models import User


class CompanySummarySerializer(serializers.Serializer):
    id   = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    nit  = serializers.CharField(read_only=True)


class UserMeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    company   = CompanySummarySerializer(read_only=True)

    class Meta:
        model  = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role', 'company']
        read_only_fields = fields

    def get_full_name(self, obj: User) -> str:
        return obj.full_name


class LoginSerializer(serializers.Serializer):
    email    = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
