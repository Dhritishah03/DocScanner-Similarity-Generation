from django.urls import path
from . import views


urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("scan/", views.scan_document, name="scan_document"),
    path("request_credits/", views.request_credits, name="request_credits"),
    path("admin/analytics/", views.admin_analytics, name="admin_analytics"),
    path("credit-request/<int:request_id>/<str:action>/", views.manage_credit_requests, name="manage_credit_requests"),  # ✅ Corrected URL name
]

