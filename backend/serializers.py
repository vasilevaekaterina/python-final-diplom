from rest_framework import serializers

from backend.models import (
    Category,
    Contact,
    Order,
    OrderItem,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)


class ContactSerializer(serializers.ModelSerializer):
    """Адрес доставки покупателя."""

    class Meta:
        model = Contact
        fields = (
            'id',
            'city',
            'street',
            'house',
            'structure',
            'building',
            'apartment',
            'user',
            'phone',
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True},
        }


class UserSerializer(serializers.ModelSerializer):
    """Профиль пользователя + вложенные контакты (только чтение)."""

    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'company',
            'position',
            'contacts',
        )
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    """Категория товаров."""

    class Meta:
        model = Category
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    """Магазин (id, имя, принимает ли заказы)."""

    class Meta:
        model = Shop
        fields = ('id', 'name', 'state')
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    """Товар: название и категория (строкой)."""

    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('name', 'category')


class ProductParameterSerializer(serializers.ModelSerializer):
    """Параметр прайса (имя + значение)."""

    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')


class ProductInfoSerializer(serializers.ModelSerializer):
    """Позиция в прайсе магазина (цена, остаток, товар, параметры)."""

    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = (
            'id',
            'model',
            'product',
            'shop',
            'quantity',
            'price',
            'price_rrc',
            'product_parameters',
        )
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    """Запись в корзине/заказе (для POST корзины)."""

    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity', 'order')
        read_only_fields = ('id',)
        extra_kwargs = {'order': {'write_only': True}}


class OrderItemReadSerializer(OrderItemSerializer):
    """Позиция заказа с вложенным ProductInfo (для ответа GET)."""

    product_info = ProductInfoSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    """
    Заказ или корзина: позиции, сумма (annotate total_sum), контакт доставки.
    """

    ordered_items = OrderItemReadSerializer(read_only=True, many=True)
    total_sum = serializers.IntegerField()
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'ordered_items',
            'state',
            'dt',
            'total_sum',
            'contact',
        )
        read_only_fields = ('id',)
