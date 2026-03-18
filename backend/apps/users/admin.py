from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display  = ['email', 'full_name', 'role', 'company', 'is_active']
    list_filter   = ['role', 'is_active', 'company']
    search_fields = ['email', 'first_name', 'last_name']
