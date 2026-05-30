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
import enum


class SyncMode(enum.Enum):
    """
    Mode for ingredient sync/import scripts.

    INSERT: bulk-insert new ingredients (very fast, use for empty databases)
    UPDATE: update existing ingredients or create new ones (slower, 2 queries per product)
    """

    INSERT = enum.auto()
    UPDATE = enum.auto()


ENERGY_FACTOR = {
    'protein': {'kg': 4, 'lb': 113},
    'carbohydrates': {'kg': 4, 'lb': 113},
    'fat': {'kg': 9, 'lb': 225},
}
"""
Simple approximation of energy (kcal) provided per gram or ounce
"""

KJ_PER_KCAL = 4.184

OFF_FULL_DUMP_URL = 'https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz'

#
# Recipe (ready-made / composite meal) portioning
#
RECIPE_UNIT_GRAM = 'g'
RECIPE_UNIT_MILLILITER = 'ml'
RECIPE_UNIT_UNIT = 'unit'
RECIPE_UNIT_PORTION = 'portion'

RECIPE_UNIT_CHOICES = [
    (RECIPE_UNIT_GRAM, 'Grams'),
    (RECIPE_UNIT_MILLILITER, 'Milliliters'),
    (RECIPE_UNIT_UNIT, 'Units'),
    (RECIPE_UNIT_PORTION, 'Portions'),
]
"""
The units a finished recipe can be divided/logged by.

Grams is always available (it is the base weight). Milliliters need a recipe
``total_volume_ml``, units need ``units_per_batch`` and portions use ``portions``.
"""
