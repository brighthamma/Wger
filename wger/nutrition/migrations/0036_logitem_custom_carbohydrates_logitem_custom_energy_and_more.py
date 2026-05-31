#  This file is part of wger Workout Manager <https://github.com/wger-project>.
#
#  wger Workout Manager is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

import django.core.validators
import django.db.models.deletion
from decimal import Decimal

from django.db import (
    migrations,
    models,
)


class Migration(migrations.Migration):
    dependencies = [
        ('nutrition', '0035_recipe_recipeitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='logitem',
            name='custom_carbohydrates',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=7, null=True),
        ),
        migrations.AddField(
            model_name='logitem',
            name='custom_energy',
            field=models.IntegerField(blank=True, null=True, verbose_name='Energy'),
        ),
        migrations.AddField(
            model_name='logitem',
            name='custom_fat',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=7, null=True),
        ),
        migrations.AddField(
            model_name='logitem',
            name='custom_name',
            field=models.CharField(
                blank=True, max_length=200, null=True, verbose_name='Custom name'
            ),
        ),
        migrations.AddField(
            model_name='logitem',
            name='custom_protein',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=7, null=True),
        ),
        migrations.AlterField(
            model_name='logitem',
            name='amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=6,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(Decimal('1')),
                    django.core.validators.MaxValueValidator(Decimal('1000')),
                ],
                verbose_name='Amount',
            ),
        ),
        migrations.AlterField(
            model_name='logitem',
            name='ingredient',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='nutrition.ingredient',
                verbose_name='Ingredient',
            ),
        ),
    ]
