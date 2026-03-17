from django.urls import path

from backend.views import (
    ConfirmAccount,
    LoginAccount,
    RegisterAccount,
)

app_name = 'backend'

urlpatterns = [
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/confirm', ConfirmAccount.as_view(), name='user-confirm'),
    path('user/login', LoginAccount.as_view(), name='user-login'),
]
