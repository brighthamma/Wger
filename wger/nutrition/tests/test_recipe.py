# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Workout Manager.  If not, see <http://www.gnu.org/licenses/>.

# Standard Library
from decimal import Decimal

# Django
from django.contrib.auth.models import User
from django.urls import reverse

# wger
from wger.core.tests.base_testcase import WgerTestCase
from wger.nutrition import models
from wger.nutrition.consts import (
    RECIPE_UNIT_GRAM,
    RECIPE_UNIT_MILLILITER,
    RECIPE_UNIT_PORTION,
    RECIPE_UNIT_UNIT,
)


class RecipeNutritionTestCase(WgerTestCase):
    """
    Tests the nutritional value calculations and portioning of a recipe
    """

    def setUp(self):
        super().setUp()
        self.ingredient = models.Ingredient.objects.get(pk=1)

        # A recipe of 2 x 100 g of ingredient #1 -> 200 g total
        self.recipe = models.Recipe(
            name='Test recipe',
            language=self.ingredient.language,
            user_id=1,
            portions=4,
            total_volume_ml=400,
            units_per_batch=8,
        )
        self.recipe.save()

        for _ in range(2):
            item = models.RecipeItem(
                recipe=self.recipe,
                ingredient=self.ingredient,
                amount=100,
                order=1,
            )
            item.save()

    def test_total_weight(self):
        self.assertEqual(self.recipe.total_weight, Decimal(200))

    def test_total_nutritional_values(self):
        values = self.recipe.get_nutritional_values()
        # 200 g -> twice the per-100g energy of the ingredient
        self.assertAlmostEqual(values.energy, self.ingredient.energy * Decimal(2), 2)

    def test_per_100g(self):
        values = self.recipe.nutritional_values_per_100g()
        self.assertAlmostEqual(values.energy, self.ingredient.energy, 2)
        self.assertAlmostEqual(values.protein, self.ingredient.protein, 2)

    def test_per_portion(self):
        # total / 4 portions == half of a 100g value (200g/4 = 50g)
        values = self.recipe.nutritional_values_per_portion()
        self.assertAlmostEqual(values.energy, self.ingredient.energy * Decimal('0.5'), 2)

    def test_values_for_grams(self):
        values = self.recipe.nutritional_values_for(100, RECIPE_UNIT_GRAM)
        self.assertAlmostEqual(values.energy, self.ingredient.energy, 2)

    def test_values_for_milliliters(self):
        # 200 ml of a 400 ml recipe == half the total
        values = self.recipe.nutritional_values_for(200, RECIPE_UNIT_MILLILITER)
        self.assertAlmostEqual(values.energy, self.ingredient.energy, 2)

    def test_values_for_units(self):
        # 2 of 8 units == quarter of total == 50 g
        values = self.recipe.nutritional_values_for(2, RECIPE_UNIT_UNIT)
        self.assertAlmostEqual(values.energy, self.ingredient.energy * Decimal('0.5'), 2)

    def test_values_for_portions(self):
        # 2 of 4 portions == half the total
        values = self.recipe.nutritional_values_for(2, RECIPE_UNIT_PORTION)
        self.assertAlmostEqual(values.energy, self.ingredient.energy, 2)

    def test_unknown_unit_raises(self):
        with self.assertRaises(ValueError):
            self.recipe.nutritional_values_for(1, 'banana')

    def test_empty_recipe_has_zero_values(self):
        empty = models.Recipe(name='Empty', language=self.ingredient.language, user_id=1)
        empty.save()
        self.assertEqual(empty.total_weight, Decimal(0))
        self.assertEqual(empty.nutritional_values_per_100g().energy, 0)
        self.assertEqual(empty.nutritional_values_for(100, RECIPE_UNIT_GRAM).energy, 0)


class RecipeMaterializeTestCase(WgerTestCase):
    """
    Tests that a recipe can be materialized into a food-database ingredient
    """

    def setUp(self):
        super().setUp()
        self.ingredient = models.Ingredient.objects.get(pk=1)
        self.recipe = models.Recipe(
            name='Materialized recipe',
            language=self.ingredient.language,
            user_id=1,
            portions=4,
            code='1234567890',
        )
        self.recipe.save()
        models.RecipeItem(
            recipe=self.recipe, ingredient=self.ingredient, amount=200, order=1
        ).save()

    def test_materialize_creates_linked_ingredient(self):
        ingredient = self.recipe.sync_to_ingredient()
        self.assertIsNotNone(ingredient)

        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.ingredient_id, ingredient.pk)

        # per-100g energy matches the source ingredient (recipe is just 200g of it)
        self.assertAlmostEqual(ingredient.energy, self.ingredient.energy, delta=1)
        self.assertEqual(ingredient.code, '1234567890')

    def test_materialize_creates_portion_weight_unit(self):
        ingredient = self.recipe.sync_to_ingredient()
        portion = ingredient.ingredientweightunit_set.filter(name='Portion').first()
        self.assertIsNotNone(portion)
        # 200 g / 4 portions = 50 g
        self.assertEqual(portion.gram, 50)

    def test_materialize_is_idempotent(self):
        first = self.recipe.sync_to_ingredient()
        second = self.recipe.sync_to_ingredient()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(
            second.ingredientweightunit_set.filter(name='Portion').count(),
            1,
        )

    def test_empty_recipe_is_not_materialized(self):
        empty = models.Recipe(name='Empty', language=self.ingredient.language, user_id=1)
        empty.save()
        self.assertIsNone(empty.sync_to_ingredient())


class RecipeApiTestCase(WgerTestCase):
    """
    Tests the recipe API endpoints (create, list, portioning action)
    """

    def test_create_and_list_recipe(self):
        self.user_login('test')
        ingredient = models.Ingredient.objects.get(pk=1)

        response = self.client.post(
            reverse('recipe-list'),
            data={'name': 'API recipe', 'language': ingredient.language_id, 'portions': 2},
        )
        self.assertEqual(response.status_code, 201)
        recipe_id = response.data['id']

        # The created recipe is owned by the logged-in user and is listed
        response = self.client.get(reverse('recipe-list'))
        self.assertEqual(response.status_code, 200)
        ids = [r['id'] for r in response.data['results']]
        self.assertIn(recipe_id, ids)

    def test_values_for_action(self):
        self.user_login('test')
        ingredient = models.Ingredient.objects.get(pk=1)
        recipe = models.Recipe(
            name='API values',
            language=ingredient.language,
            user=User.objects.get(username='test'),
            portions=2,
        )
        recipe.save()
        models.RecipeItem(recipe=recipe, ingredient=ingredient, amount=100, order=1).save()

        response = self.client.get(
            reverse('recipe-values-for', kwargs={'pk': recipe.pk}),
            data={'amount': 100, 'unit': RECIPE_UNIT_GRAM},
        )
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(float(response.data['energy']), float(ingredient.energy), delta=1)

    def test_values_for_invalid_unit(self):
        self.user_login('test')
        ingredient = models.Ingredient.objects.get(pk=1)
        recipe = models.Recipe(
            name='Bad unit',
            language=ingredient.language,
            user=User.objects.get(username='test'),
        )
        recipe.save()

        response = self.client.get(
            reverse('recipe-values-for', kwargs={'pk': recipe.pk}),
            data={'amount': 1, 'unit': 'banana'},
        )
        self.assertEqual(response.status_code, 400)
