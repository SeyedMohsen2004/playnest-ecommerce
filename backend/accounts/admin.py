from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.forms import UserChangeForm, UserCreationForm
from accounts.models import PhoneOTP, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = (
        "phone_number",
        "first_name",
        "last_name",
        "email",
        "is_phone_verified",
        "is_active",
        "is_staff",
        "date_joined",
    )
    search_fields = ("phone_number", "first_name", "last_name", "email")
    list_filter = ("is_phone_verified", "is_active", "is_staff", "date_joined")
    ordering = ("-date_joined",)
    readonly_fields = ("password", "date_joined", "last_login")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "phone_number",
                    "password",
                    "first_name",
                    "last_name",
                    "email",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "is_phone_verified",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone_number",
                    "first_name",
                    "last_name",
                    "email",
                    "password1",
                    "password2",
                    "is_phone_verified",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = (
        "phone_number",
        "code",
        "purpose",
        "is_used",
        "expires_at",
        "created_at",
        "verified_at",
    )
    search_fields = ("phone_number",)
    list_filter = ("purpose", "is_used", "created_at")
    readonly_fields = (
        "code",
        "created_at",
        "verified_at",
    )
