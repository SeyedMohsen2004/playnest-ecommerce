from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.forms import UserChangeForm, UserCreationForm
from accounts.models import LoginThrottle, PhoneOTP, User


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
    list_filter = (
        "is_phone_verified",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )
    ordering = ("-date_joined",)
    readonly_fields = ("password", "date_joined", "last_login")
    date_hierarchy = "date_joined"
    fieldsets = (
        (
            "Customer information",
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
            "Account status",
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
        "user",
        "purpose",
        "delivery_status",
        "failed_attempts",
        "is_used",
        "is_expired_display",
        "expires_at",
        "created_at",
        "verified_at",
    )
    search_fields = ("phone_number",)
    list_filter = (
        "purpose",
        "delivery_status",
        "is_used",
        "created_at",
        "expires_at",
    )
    readonly_fields = (
        "phone_number",
        "user",
        "purpose",
        "delivery_status",
        "failed_attempts",
        "is_used",
        "expires_at",
        "created_at",
        "sent_at",
        "verified_at",
        "invalidated_at",
        "locked_at",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    fieldsets = (
        (
            "OTP request",
            {
                "fields": (
                    "phone_number",
                    "user",
                    "purpose",
                    "delivery_status",
                    "failed_attempts",
                    "is_used",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "sent_at",
                    "expires_at",
                    "verified_at",
                    "invalidated_at",
                    "locked_at",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(boolean=True, description="Expired")
    def is_expired_display(self, obj):
        return obj.is_expired()


@admin.register(LoginThrottle)
class LoginThrottleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "failed_attempts",
        "window_started_at",
        "blocked_until",
        "updated_at",
    )
    readonly_fields = (
        "identifier_hash",
        "failed_attempts",
        "window_started_at",
        "blocked_until",
        "updated_at",
    )
    ordering = ("-updated_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
