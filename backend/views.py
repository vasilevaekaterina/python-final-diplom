from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from django.db.models import Q
from requests import get
from rest_framework.authtoken.models import Token
from yaml import load as load_yaml, Loader
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import (
    Category,
    ConfirmEmailToken,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)
from backend.serializers import (
    CategorySerializer,
    ProductInfoSerializer,
    ShopSerializer,
    UserSerializer,
)


class PartnerPermissionMixin:
    """
    Доступ к эндпоинтам /api/v1/partner/* только у пользователей с type='shop'.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'Status': False, 'Error': 'Log in required'},
                status=403,
            )
        if getattr(request.user, 'type', None) != 'shop':
            return JsonResponse(
                {'Status': False, 'Error': 'Только для магазинов'},
                status=403,
            )
        return super().dispatch(request, *args, **kwargs)


class PartnerBaseView(PartnerPermissionMixin, APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


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


class LoginAccount(APIView):
    def post(self, request, *args, **kwargs):
        if not {'email', 'password'}.issubset(request.data):
            return JsonResponse(
                {
                    'Status': False,
                    'Errors': 'Не указаны все необходимые аргументы',
                },
            )

        user = authenticate(
            request,
            username=request.data['email'],
            password=request.data['password'],
        )

        if user is None or not user.is_active:
            return JsonResponse(
                {
                    'Status': False,
                    'Errors': 'Не удалось авторизовать',
                },
            )

        token, _ = Token.objects.get_or_create(user=user)
        return JsonResponse({'Status': True, 'Token': token.key})


class AccountDetails(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if 'password' in request.data:
            try:
                validate_password(request.data['password'], user=request.user)
            except ValidationError as password_error:
                error_array = [str(item) for item in password_error]
                return JsonResponse(
                    {
                        'Status': False,
                        'Errors': {'password': error_array},
                    },
                )
            request.user.set_password(request.data['password'])
            request.user.save(update_fields=['password'])

        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'Status': True})

        return JsonResponse(
            {
                'Status': False,
                'Errors': serializer.errors,
            },
        )


class ApiRoot(APIView):
    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {
                'Status': True,
                'Message': 'API is running',
                'Endpoints': {
                    'register': '/api/v1/user/register',
                    'confirm': '/api/v1/user/confirm',
                    'login': '/api/v1/user/login',
                    'details': '/api/v1/user/details',
                    'password_reset': '/api/v1/user/password_reset',
                    'password_reset_confirm': (
                        '/api/v1/user/password_reset/confirm'
                    ),
                    'categories': '/api/v1/categories',
                    'shops': '/api/v1/shops',
                    'products': '/api/v1/products',
                    'partner_update': '/api/v1/partner/update',
                    'partner_state': '/api/v1/partner/state',
                    'partner_orders': '/api/v1/partner/orders',
                },
            },
        )


class CategoryView(APIView):
    def get(self, request, *args, **kwargs):
        queryset = Category.objects.all().order_by('-name')
        serializer = CategorySerializer(queryset, many=True)
        return Response(serializer.data)


class ShopView(APIView):
    def get(self, request, *args, **kwargs):
        queryset = Shop.objects.filter(state=True).order_by('-name')
        serializer = ShopSerializer(queryset, many=True)
        return Response(serializer.data)


class ProductInfoView(APIView):
    def get(self, request, *args, **kwargs):
        query = Q(shop__state=True)

        shop_id = request.query_params.get('shop_id')
        if shop_id:
            query &= Q(shop_id=shop_id)

        category_id = request.query_params.get('category_id')
        if category_id:
            query &= Q(product__category_id=category_id)

        search = request.query_params.get('search')
        if search:
            query &= (
                Q(product__name__icontains=search)
                | Q(model__icontains=search)
            )

        queryset = (
            ProductInfo.objects.filter(query)
            .select_related('shop', 'product__category')
            .prefetch_related('product_parameters__parameter')
            .distinct()
        )
        serializer = ProductInfoSerializer(queryset, many=True)
        return Response(serializer.data)


class PartnerUpdate(PartnerBaseView):
    """POST: загрузка прайса по URL (YAML)."""

    def post(self, request, *args, **kwargs):
        url = request.data.get('url')
        if not url:
            return JsonResponse(
                {
                    'Status': False,
                    'Errors': 'Не указаны все необходимые аргументы',
                },
            )

        validator = URLValidator()
        try:
            validator(url)
        except ValidationError as exc:
            return JsonResponse(
                {'Status': False, 'Error': str(exc)},
            )

        try:
            response = get(url)
            response.raise_for_status()
            stream = response.content
        except Exception as exc:
            return JsonResponse(
                {'Status': False, 'Error': str(exc)},
            )

        try:
            data = load_yaml(stream, Loader=Loader)
        except Exception as exc:
            return JsonResponse(
                {'Status': False, 'Error': f'Ошибка разбора YAML: {exc}'},
            )

        if not data or 'shop' not in data or 'categories' not in data:
            return JsonResponse(
                {
                    'Status': False,
                    'Error': 'Неверная структура YAML: shop, categories',
                },
            )

        shop, _ = Shop.objects.get_or_create(
            user=request.user,
            defaults={'name': data['shop']},
        )
        shop.name = data['shop']
        shop.save(update_fields=['name'])

        for cat in data.get('categories', []):
            category, _ = Category.objects.get_or_create(
                id=cat['id'],
                defaults={'name': cat['name']},
            )
            category.name = cat['name']
            category.save(update_fields=['name'])
            category.shops.add(shop)

        ProductInfo.objects.filter(shop=shop).delete()

        for item in data.get('goods', []):
            product, _ = Product.objects.get_or_create(
                name=item['name'],
                category_id=item['category'],
            )
            product_info = ProductInfo.objects.create(
                product=product,
                shop=shop,
                external_id=item['id'],
                model=item.get('model', ''),
                price=item['price'],
                price_rrc=item['price_rrc'],
                quantity=item['quantity'],
            )
            for param_name, param_value in item.get('parameters', {}).items():
                param_obj, _ = Parameter.objects.get_or_create(
                    name=param_name,
                )
                ProductParameter.objects.create(
                    product_info=product_info,
                    parameter=param_obj,
                    value=str(param_value),
                )

        return JsonResponse({'Status': True})


class PartnerState(PartnerBaseView):
    """GET: статус приёма заказов; POST: изменить статус."""

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {'Status': True, 'Message': 'Partner state (stub)'},
        )

    def post(self, request, *args, **kwargs):
        return JsonResponse(
            {'Status': True, 'Message': 'Partner state update (stub)'},
        )


class PartnerOrders(PartnerBaseView):
    """GET: заказы поставщика."""

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {'Status': True, 'Orders': []},
        )
