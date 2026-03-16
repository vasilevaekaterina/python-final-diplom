from django.contrib import admin

from backend.models import (
    Category,
    ConfirmEmailToken,
    Contact,
    Order,
    OrderItem,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'type', 'is_active')
    list_filter = ('type', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'url', 'user')
    list_filter = ('state',)
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class ProductParameterInline(admin.TabularInline):
    model = ProductParameter
    extra = 1


class ProductInfoInline(admin.TabularInline):
    model = ProductInfo
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)
    inlines = (ProductInfoInline,)


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'shop',
        'external_id',
        'model',
        'quantity',
        'price',
        'price_rrc',
    )
    list_filter = ('shop', 'product')
    search_fields = ('product__name', 'shop__name', 'external_id')
    inlines = (ProductParameterInline,)


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    list_display = ('product_info', 'parameter', 'value')
    list_filter = ('parameter',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'street', 'house', 'phone')
    search_fields = ('city', 'street', 'phone', 'user__email')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'dt', 'state', 'contact')
    list_filter = ('state', 'dt')
    search_fields = ('user__email',)
    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_info', 'quantity')
    list_filter = ('order',)


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at')
    search_fields = ('user__email', 'key')
