#  This file is part of wger Workout Manager <https://github.com/wger-project>.
#
#  wger Workout Manager is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

import django.core.validators
import django.db.models.deletion
import wger.nutrition.helpers
import wger.utils.uuid
from decimal import Decimal

from django.conf import settings
from django.db import (
    migrations,
    models,
)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0022_move_email_verified_to_emailaddress'),
        ('nutrition', '0034_ingredient_trigram_gin_index'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Recipe',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'uuid',
                    models.UUIDField(
                        default=wger.utils.uuid.uuid7,
                        editable=False,
                        unique=True,
                        verbose_name='UUID',
                    ),
                ),
                (
                    'is_public',
                    models.BooleanField(
                        default=False,
                        help_text='Public recipes are visible to and usable by all users',
                        verbose_name='Public',
                    ),
                ),
                (
                    'name',
                    models.CharField(
                        max_length=200,
                        validators=[django.core.validators.MinLengthValidator(3)],
                        verbose_name='Name',
                    ),
                ),
                ('code', models.CharField(blank=True, db_index=True, max_length=200, null=True)),
                (
                    'portions',
                    models.PositiveSmallIntegerField(
                        default=1,
                        help_text='How many portions the whole recipe yields',
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name='Portions',
                    ),
                ),
                (
                    'total_volume_ml',
                    models.PositiveIntegerField(
                        blank=True,
                        help_text='Total volume of the finished recipe, required to divide it by milliliters',
                        null=True,
                        verbose_name='Total volume (ml)',
                    ),
                ),
                (
                    'units_per_batch',
                    models.PositiveIntegerField(
                        blank=True,
                        help_text='How many discrete units the recipe yields (e.g. 12 cookies), required to divide it by units',
                        null=True,
                        verbose_name='Units per batch',
                    ),
                ),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Date')),
                ('last_update', models.DateTimeField(auto_now=True, verbose_name='Date')),
                (
                    'ingredient',
                    models.OneToOneField(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='recipe',
                        to='nutrition.ingredient',
                        verbose_name='Materialized ingredient',
                    ),
                ),
                (
                    'language',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='core.language',
                        verbose_name='Language',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='User',
                    ),
                ),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='RecipeItem',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'order',
                    models.IntegerField(
                        blank=True, default=1, editable=False, verbose_name='Order'
                    ),
                ),
                (
                    'amount',
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=6,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal('1')),
                            django.core.validators.MaxValueValidator(Decimal('1000')),
                        ],
                        verbose_name='Amount',
                    ),
                ),
                (
                    'ingredient',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='nutrition.ingredient',
                        verbose_name='Ingredient',
                    ),
                ),
                (
                    'recipe',
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to='nutrition.recipe',
                        verbose_name='Recipe',
                    ),
                ),
                (
                    'weight_unit',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to='nutrition.ingredientweightunit',
                        verbose_name='Weight unit',
                    ),
                ),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(wger.nutrition.helpers.BaseMealItem, models.Model),
        ),
    ]
