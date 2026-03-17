from django.urls import path
from django_rest_passwordreset.views import (
    reset_password_confirm,
    reset_password_request_token,
)

from backend.views import (
    AccountDetails,
    ConfirmAccount,
    LoginAccount,
    RegisterAccount,
)

app_name = 'backend'

urlpatterns = [
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/confirm', ConfirmAccount.as_view(), name='user-confirm'),
    path('user/login', LoginAccount.as_view(), name='user-login'),
    path('user/details', AccountDetails.as_view(), name='user-details'),
    path('user/password_reset', reset_password_request_token, name='password-reset'),
    path(
        'user/password_reset/confirm',
        reset_password_confirm,
        name='password-reset-confirm',
    ),
]
