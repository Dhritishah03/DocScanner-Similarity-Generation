from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import Profile
from .models import CreditRequest

User = get_user_model()

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ["username", "email", "is_staff", "is_active"]

admin.site.register(User, CustomUserAdmin)
admin.site.register(CreditRequest)
admin.site.register(Profile)


