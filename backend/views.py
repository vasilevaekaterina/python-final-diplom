from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from rest_framework.views import APIView

from backend.models import ConfirmEmailToken, User


class RegisterAccount(APIView):
    def post(self, request, *args, **kwargs):
        required_fields = {
            'first_name',
            'last_name',
            'email',
            'password',
            'company',
            'position',
        }
        if not required_fields.issubset(request.data):
            return JsonResponse(
                {
                    'Status': False,
                    'Errors': 'Не указаны все необходимые аргументы',
                },
            )

        user_type = request.data.get('type', 'buyer')
        if user_type not in {'buyer', 'shop'}:
            return JsonResponse(
                {
                    'Status': False,
                    'Errors': {'type': 'Допустимые значения: buyer или shop'},
                },
            )

        try:
            validate_password(request.data['password'])
        except ValidationError as password_error:
            error_array = [str(item) for item in password_error]
            return JsonResponse(
                {
                    'Status': False,
                    'Errors': {'password': error_array},
                },
            )

        try:
            user = User.objects.create_user(
                email=request.data['email'],
                password=request.data['password'],
                first_name=request.data['first_name'],
                last_name=request.data['last_name'],
                company=request.data['company'],
                position=request.data['position'],
                type=user_type,
            )
        except Exception as exc:
            return JsonResponse(
                {
                    'Status': False,
                    'Errors': str(exc),
                },
            )

        confirm_token = ConfirmEmailToken.objects.create(user=user)
        return JsonResponse(
            {
                'Status': True,
                'Token': confirm_token.key,
            },
        )


class ConfirmAccount(APIView):
    def post(self, request, *args, **kwargs):
        if not {'email', 'token'}.issubset(request.data):
            return JsonResponse(
                {
                    'Status': False,
                    'Errors': 'Не указаны все необходимые аргументы',
                },
            )

        token = ConfirmEmailToken.objects.filter(
            user__email=request.data['email'],
            key=request.data['token'],
        ).first()

        if not token:
            return JsonResponse(
                {
                    'Status': False,
                    'Errors': 'Неправильно указан токен или email',
                },
            )

        token.user.is_active = True
        token.user.save()
        token.delete()
        return JsonResponse({'Status': True})
