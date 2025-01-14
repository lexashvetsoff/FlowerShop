from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.functions import TruncDate
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

User = get_user_model()


class Event(models.Model):
    name = models.CharField('название', max_length=200, unique=True)

    class Meta:
        verbose_name = 'событие для букета'
        verbose_name_plural = 'события для букета'

    def __str__(self):
        return self.name


class Bouquet(models.Model):
    name = models.CharField('название', max_length=100, unique=True)
    description = models.TextField('описание')
    photo = models.ImageField('фото')
    price = models.DecimalField('цена', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    height_cm = models.PositiveSmallIntegerField(
        'высота',
        validators=[MinValueValidator(0)],
        help_text='задается в сантиметрах'
    )
    width_cm = models.PositiveSmallIntegerField(
        'ширина',
        validators=[MinValueValidator(0)],
        help_text='задается в сантиметрах'
    )
    events = models.ManyToManyField(Event)
    is_recommended = models.BooleanField('рекомендованный', default=False)

    class Meta:
        verbose_name = 'букет'
        verbose_name_plural = 'букеты'

    def __str__(self):
        return self.name


class BouquetItem(models.Model):
    name = models.CharField('название', max_length=200, unique=True)
    bouquets = models.ManyToManyField(Bouquet, through='BouquetItemsInBouquet')

    class Meta:
        verbose_name = 'элемент букета'
        verbose_name_plural = 'элементы букетов'

    def __str__(self):
        return self.name


class BouquetItemsInBouquet(models.Model):
    bouquet = models.ForeignKey(Bouquet, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(BouquetItem, related_name='bouquet_relations', on_delete=models.CASCADE)
    count = models.PositiveSmallIntegerField('количество', validators=[MinValueValidator(1)], default=1)

    class Meta:
        verbose_name = 'элемент букета в букете'
        verbose_name_plural = 'элементы букета в букете'
        unique_together = [['bouquet', 'item']]

    def __str__(self):
        return f'{self.item} в {self.bouquet} ({self.count} шт.)'


class FlowerShop(models.Model):
    address = models.CharField('адрес', max_length=200, unique=True)
    phone = PhoneNumberField('контактный номер', region='RU', blank=True)  # TODO: migration for remove blank

    class Meta:
        verbose_name = 'магазин цветов'
        verbose_name_plural = 'магазины цветов'

    def __str__(self):
        return self.address

class FlowerShopCatalogItem(models.Model):
    flower_shop = models.ForeignKey(
        FlowerShop,
        related_name='catalog_items',
        verbose_name='магазин цветов',
        on_delete=models.CASCADE,
    )
    bouquet = models.ForeignKey(
        Bouquet,
        on_delete=models.CASCADE,
        related_name='catalog_items',
        verbose_name='букет',
    )
    availability = models.BooleanField(
        'в наличии',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт каталога магазина цветов'
        verbose_name_plural = 'пункты каталога магазина цветов'
        unique_together = [['flower_shop', 'bouquet']]

    def __str__(self):
        return f'{self.flower_shop.address} - {self.bouquet.name}'


class DeliveryWindow(models.Model):
    name = models.CharField('название', max_length=200, unique=True)
    from_hour = models.PositiveSmallIntegerField(
        'доставить с',
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        null=True,
        blank=True
    )
    to_hour = models.PositiveSmallIntegerField(
        'доставить до',
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'окно доставки'
        verbose_name_plural = 'окна доставки'
        unique_together = [['from_hour', 'to_hour']]

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        created = 'создан'
        composing = 'собирается'
        composed = 'собран'
        delivering = 'доставляется'
        delivered = 'доставлен'
        cancelled = 'отменен'

    bouquet = models.ForeignKey(Bouquet, related_name='orders', on_delete=models.DO_NOTHING)
    price = models.DecimalField(  # price of bouquet can change
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    client_name = models.CharField('имя клиента', max_length=200)
    phone = PhoneNumberField('контактный номер', region='RU')
    delivery_address = models.CharField('адрес доставки', max_length=200)
    delivery_window = models.ForeignKey(
        DeliveryWindow,
        related_name='orders',
        on_delete=models.DO_NOTHING,
        null=True,  # null if ASAP
        blank=True
    )
    email = models.EmailField('email адрес', blank=True)
    paid = models.BooleanField('оплачен')
    comment = models.TextField('комментарий', blank=True)
    created_at = models.DateTimeField('дата и время создания заказа', default=timezone.now)
    composed_at = models.DateTimeField('дата и время сбора букета флористом', null=True, blank=True)
    delivered_at = models.DateTimeField('дата и время доставки букета', null=True, blank=True)
    status = models.CharField(
        'статус заказа',
        max_length=15,
        choices=Status.choices,
        default=Status.created,
        db_index=True
    )
    florist = models.ForeignKey(User, related_name='f_orders', on_delete=models.DO_NOTHING, null=True, blank=True)
    courier = models.ForeignKey(User, related_name='c_orders', on_delete=models.DO_NOTHING, null=True, blank=True)

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        indexes = [models.Index(TruncDate("created_at"), "created_at", name="order_created_at_date_idx")]

    def __str__(self):
        return f'Заказ {self.pk} ({self.created_at}), {self.bouquet} по адресу {self.delivery_address}'


class Consultation(models.Model):
    class Status(models.TextChoices):
        created = 'создана'
        consulted = 'оказана'
        cancelled = 'отменена (не доступен)'

    client_name = models.CharField('имя клиента', max_length=200)
    phone = PhoneNumberField('контактный номер', region='RU')
    created_at = models.DateTimeField('дата и время заказа консультации', default=timezone.now)
    consulted_at = models.DateTimeField('дата и время оказания консультации', null=True, blank=True)
    status = models.CharField(
        'статус консультации',
        max_length=30,
        choices=Status.choices,
        default=Status.created,
        db_index=True
    )
    event = models.CharField('повод', max_length=100, blank=True)
    budget = models.CharField('бюджет', max_length=100, blank=True)

    class Meta:
        verbose_name = 'консультация'
        verbose_name_plural = 'консультации'
        indexes = [models.Index(TruncDate("created_at"), "created_at", name="cons_created_at_date_idx")]

    def __str__(self):
        return f'Консультация {self.pk} ({self.created_at}), {self.phone} ({self.client_name})'
