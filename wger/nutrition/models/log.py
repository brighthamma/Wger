#  This file is part of wger Workout Manager <https://github.com/wger-project>.
#  Copyright (C) 2013 - 2021 wger Team
#
#  wger Workout Manager is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  wger Workout Manager is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Standard Library
from decimal import Decimal

# Django
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.utils import timezone

# wger
from wger.nutrition.helpers import (
    BaseMealItem,
    NutritionalValues,
)

# Local
from .ingredient import Ingredient
from .ingredient_weight_unit import IngredientWeightUnit
from .meal import Meal
from .plan import NutritionPlan


class LogItem(BaseMealItem, models.Model):
    """
    An item (component) of a log
    """

    # Metaclass to set some other properties
    class Meta:
        ordering = [
            '-datetime',
        ]

    plan = models.ForeignKey(
        NutritionPlan,
        verbose_name='Nutrition plan',
        on_delete=models.CASCADE,
    )
    """
    The plan this log belongs to
    """

    meal = models.ForeignKey(
        Meal,
        verbose_name='Meal',
        on_delete=models.SET_NULL,
        related_name='log_items',
        blank=True,
        null=True,
    )
    """
    The meal this log belongs to (optional)
    """

    datetime = models.DateTimeField(verbose_name='Date and Time (Approx.)', default=timezone.now)
    """
    Time and date when the log was added
    """

    comment = models.TextField(
        verbose_name='Comment',
        blank=True,
        null=True,
    )
    """
    Comment field, for additional information
    """

    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ingredient',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    """
    Ingredient (empty for custom entries with manually entered values)
    """

    custom_name = models.CharField(
        max_length=200,
        verbose_name='Custom name',
        null=True,
        blank=True,
    )
    """Optional label for a custom entry (no ingredient)"""

    custom_energy = models.IntegerField(verbose_name='Energy', null=True, blank=True)
    custom_protein = models.DecimalField(
        decimal_places=3, max_digits=7, null=True, blank=True
    )
    custom_carbohydrates = models.DecimalField(
        decimal_places=3, max_digits=7, null=True, blank=True
    )
    custom_fat = models.DecimalField(decimal_places=3, max_digits=7, null=True, blank=True)
    """Manually entered nutritional values for a custom entry (totals, not per 100g)"""

    weight_unit = models.ForeignKey(
        IngredientWeightUnit,
        verbose_name='Weight unit',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    """
    Weight unit used (grams, slices, etc.)
    """

    amount = models.DecimalField(
        decimal_places=2,
        max_digits=6,
        verbose_name='Amount',
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal(1)), MaxValueValidator(Decimal(1000))],
    )
    """
    The amount of units (not used for custom entries)
    """

    @property
    def is_custom(self):
        """A custom entry has manually entered values and no ingredient"""
        return self.ingredient_id is None

    def get_nutritional_values(self, use_metric=True) -> NutritionalValues:
        """
        For custom entries the stored values are the totals for the entry;
        otherwise fall back to the ingredient-based calculation.
        """
        if self.is_custom:
            return NutritionalValues(
                energy=self.custom_energy or 0,
                protein=self.custom_protein or 0,
                carbohydrates=self.custom_carbohydrates or 0,
                fat=self.custom_fat or 0,
            )
        return super().get_nutritional_values(use_metric=use_metric)

    def __str__(self):
        """
        Return a more human-readable representation
        """
        return f'Diary entry for {self.datetime}, plan {self.plan.pk}'

    def get_owner_object(self):
        """
        Returns the object that has owner information
        """
        return self.plan
