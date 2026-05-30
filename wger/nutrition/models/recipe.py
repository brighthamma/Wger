#  This file is part of wger Workout Manager <https://github.com/wger-project>.
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
import logging
from decimal import Decimal

# Django
from django.contrib.auth.models import User
from django.core.validators import (
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models

# wger
from wger.core.models import Language
from wger.nutrition.consts import (
    RECIPE_UNIT_GRAM,
    RECIPE_UNIT_MILLILITER,
    RECIPE_UNIT_PORTION,
    RECIPE_UNIT_UNIT,
)
from wger.nutrition.helpers import NutritionalValues
from wger.utils.uuid import uuid7


logger = logging.getLogger(__name__)


class Recipe(models.Model):
    """
    A ready-made / composite meal, built from several ingredients.

    A recipe behaves like a reusable "food": its nutritional values are the
    sum of its items and it can be divided by grams, milliliters, units or
    portions. Optionally it materializes a linked :class:`Ingredient` so it
    shows up in the food database and can be searched, scanned and logged like
    any other ingredient.
    """

    class Meta:
        ordering = [
            'name',
        ]

    uuid = models.UUIDField(
        default=uuid7,
        unique=True,
        editable=False,
        verbose_name='UUID',
    )

    language = models.ForeignKey(
        Language,
        verbose_name='Language',
        on_delete=models.CASCADE,
    )

    user = models.ForeignKey(
        User,
        verbose_name='User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    """Owner of the recipe. ``None`` means it is a shared / global recipe."""

    is_public = models.BooleanField(
        verbose_name='Public',
        default=False,
        help_text='Public recipes are visible to and usable by all users',
    )

    name = models.CharField(
        max_length=200,
        verbose_name='Name',
        validators=[MinLengthValidator(3)],
    )

    code = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        db_index=True,
    )
    """Optional barcode, so the ready-made meal can be scanned like a product"""

    portions = models.PositiveSmallIntegerField(
        verbose_name='Portions',
        default=1,
        validators=[MinValueValidator(1)],
        help_text='How many portions the whole recipe yields',
    )

    total_volume_ml = models.PositiveIntegerField(
        verbose_name='Total volume (ml)',
        null=True,
        blank=True,
        help_text='Total volume of the finished recipe, required to divide it by milliliters',
    )

    units_per_batch = models.PositiveIntegerField(
        verbose_name='Units per batch',
        null=True,
        blank=True,
        help_text='How many discrete units the recipe yields (e.g. 12 cookies), '
        'required to divide it by units',
    )

    ingredient = models.OneToOneField(
        'nutrition.Ingredient',
        verbose_name='Materialized ingredient',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name='recipe',
    )
    """The food-database ingredient generated from this recipe, if materialized"""

    created = models.DateTimeField(
        verbose_name='Date',
        auto_now_add=True,
    )

    last_update = models.DateTimeField(
        verbose_name='Date',
        auto_now=True,
        editable=False,
    )

    def __str__(self):
        return self.name

    def get_owner_object(self):
        """
        Returns the object that has owner information

        Returns ``self`` (which carries the ``user`` attribute) to match the
        convention of :class:`NutritionPlan`. Read access to public recipes is
        handled at the viewset level, not here.
        """
        return self

    #
    # Nutrition
    #
    def get_nutritional_values(self, use_metric=True) -> NutritionalValues:
        """
        Sums the nutritional info of all items, i.e. the values for the whole recipe
        """
        values = NutritionalValues()
        for item in self.recipeitem_set.select_related('ingredient', 'weight_unit'):
            values += item.get_nutritional_values(use_metric=use_metric)
        return values

    @property
    def total_weight(self) -> Decimal:
        """
        Total weight of the recipe in grams (sum of all item base weights)
        """
        weight = Decimal(0)
        for item in self.recipeitem_set.select_related('weight_unit'):
            if item.weight_unit:
                weight += item.amount * Decimal(item.weight_unit.gram)
            else:
                weight += item.amount
        return weight

    #
    # Portioning
    #
    def nutritional_values_per_100g(self) -> NutritionalValues:
        weight = self.total_weight
        if not weight:
            return NutritionalValues()
        return self.get_nutritional_values() * (Decimal(100) / weight)

    def nutritional_values_per_portion(self) -> NutritionalValues:
        if not self.portions:
            return NutritionalValues()
        return self.get_nutritional_values() * (Decimal(1) / Decimal(self.portions))

    def nutritional_values_per_unit(self) -> NutritionalValues:
        if not self.units_per_batch:
            return NutritionalValues()
        return self.get_nutritional_values() * (Decimal(1) / Decimal(self.units_per_batch))

    def nutritional_values_for(self, amount, unit: str = RECIPE_UNIT_GRAM) -> NutritionalValues:
        """
        Nutritional values for ``amount`` of the recipe expressed in ``unit``.

        :param amount: how many grams/ml/units/portions
        :param unit: one of the ``RECIPE_UNIT_*`` constants
        """
        amount = Decimal(str(amount))

        if unit == RECIPE_UNIT_GRAM:
            weight = self.total_weight
            if not weight:
                return NutritionalValues()
            return self.get_nutritional_values() * (amount / weight)

        if unit == RECIPE_UNIT_MILLILITER:
            # Use the explicit volume if given, otherwise fall back to 1 g/ml
            volume = Decimal(self.total_volume_ml) if self.total_volume_ml else self.total_weight
            if not volume:
                return NutritionalValues()
            return self.get_nutritional_values() * (amount / volume)

        if unit == RECIPE_UNIT_UNIT:
            return self.nutritional_values_per_unit() * amount

        if unit == RECIPE_UNIT_PORTION:
            return self.nutritional_values_per_portion() * amount

        raise ValueError(f'Unknown recipe unit: {unit}')

    #
    # Food-database materialization
    #
    def sync_to_ingredient(self):
        """
        Create or update a linked :class:`Ingredient` so the recipe shows up in
        the food database and can be searched, scanned and logged like any other
        product.

        The ingredient stores the recipe's nutritional values per 100 g and gets
        weight units for "Portion" (and "Unit" / "ml" when applicable) so it can
        be divided the same way as the recipe itself.
        """
        # Local import to avoid a model import cycle
        # wger
        from wger.nutrition.models import (
            Ingredient,
            IngredientWeightUnit,
        )

        weight = self.total_weight
        if not weight:
            logger.info('Recipe %s has no weight, skipping ingredient sync', self.pk)
            return None

        per_100g = self.nutritional_values_per_100g()

        ingredient = self.ingredient or Ingredient()
        ingredient.language = self.language
        ingredient.name = self.name
        ingredient.code = self.code
        ingredient.energy = int(round(per_100g.energy))
        ingredient.protein = per_100g.protein
        ingredient.carbohydrates = per_100g.carbohydrates
        ingredient.carbohydrates_sugar = per_100g.carbohydrates_sugar
        ingredient.fat = per_100g.fat
        ingredient.fat_saturated = per_100g.fat_saturated
        ingredient.fiber = per_100g.fiber
        ingredient.sodium = per_100g.sodium
        ingredient.source_name = 'wger recipe'
        ingredient.save()

        # Keep the link both ways
        if self.ingredient_id != ingredient.pk:
            self.ingredient = ingredient
            self.save(update_fields=['ingredient'])

        # (Re)create the portioning weight units
        portion_gram = int(round(weight / self.portions)) if self.portions else None
        units = {}
        if portion_gram:
            units['Portion'] = portion_gram
        if self.units_per_batch:
            units['Unit'] = int(round(weight / self.units_per_batch))
        if self.total_volume_ml:
            units['ml'] = max(1, int(round(weight / self.total_volume_ml)))

        for name, gram in units.items():
            IngredientWeightUnit.objects.update_or_create(
                ingredient=ingredient,
                name=name,
                defaults={'gram': gram},
            )

        return ingredient
