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

# Standard Library
import logging

# Django
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import (
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
)

# wger
from wger.nutrition.forms import (
    RecipeForm,
    RecipeItemForm,
)
from wger.nutrition.models import (
    Recipe,
    RecipeItem,
)
from wger.utils.generic_views import (
    WgerDeleteMixin,
    WgerFormMixin,
)
from wger.utils.language import load_language


logger = logging.getLogger(__name__)


class RecipeOverviewView(LoginRequiredMixin, ListView):
    """
    Overview of all the user's ready-made meals (recipes)
    """

    model = Recipe
    template_name = 'recipe/overview.html'
    context_object_name = 'recipes'

    def get_queryset(self):
        return Recipe.objects.filter(user=self.request.user).order_by('name')


class RecipeDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view of a recipe, with its items and portioning values
    """

    model = Recipe
    template_name = 'recipe/view.html'
    context_object_name = 'recipe'

    def dispatch(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.user != request.user and not recipe.is_public:
            return HttpResponseForbidden('You are not allowed to access this object')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.object
        context['items'] = recipe.recipeitem_set.select_related('ingredient', 'weight_unit')
        context['nutritional_values'] = recipe.get_nutritional_values()
        context['per_portion'] = recipe.nutritional_values_per_portion()
        context['per_100g'] = recipe.nutritional_values_per_100g()
        return context


class RecipeCreateView(WgerFormMixin, LoginRequiredMixin, CreateView):
    """
    Create a new recipe
    """

    model = Recipe
    form_class = RecipeForm
    title = gettext_lazy('Add a ready-made meal')

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.language = load_language(self.request.LANGUAGE_CODE)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('nutrition:recipe:view', kwargs={'pk': self.object.pk})


class RecipeDeleteView(WgerDeleteMixin, LoginRequiredMixin, DeleteView):
    """
    Delete a recipe
    """

    model = Recipe
    title = gettext_lazy('Delete recipe')

    def get_queryset(self):
        return Recipe.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('nutrition:recipe:overview')


class RecipeItemCreateView(WgerFormMixin, LoginRequiredMixin, CreateView):
    """
    Add an ingredient to a recipe
    """

    model = RecipeItem
    form_class = RecipeItemForm
    title = gettext_lazy('Add ingredient to recipe')

    def get_recipe(self):
        return get_object_or_404(Recipe, pk=self.kwargs['recipe_pk'], user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        # Ensure the recipe exists and belongs to the user before doing anything
        if request.user.is_authenticated:
            self.get_recipe()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.recipe = self.get_recipe()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('nutrition:recipe:view', kwargs={'pk': self.kwargs['recipe_pk']})


def recipe_materialize(request, pk):
    """
    Create / refresh the food-database ingredient for a recipe
    """
    recipe = get_object_or_404(Recipe, pk=pk, user=request.user)
    ingredient = recipe.sync_to_ingredient()
    if ingredient is None:
        messages.warning(
            request,
            gettext_lazy('Add at least one ingredient before adding the meal to the food database.'),
        )
    else:
        messages.success(
            request,
            gettext_lazy('"%(name)s" was added to the food database.') % {'name': recipe.name},
        )
    return HttpResponseRedirect(reverse('nutrition:recipe:view', kwargs={'pk': pk}))


def recipe_item_delete(request, recipe_pk, pk):
    """
    Delete an item from a recipe
    """
    item = get_object_or_404(RecipeItem, pk=pk, recipe__pk=recipe_pk, recipe__user=request.user)
    item.delete()
    return HttpResponseRedirect(reverse('nutrition:recipe:view', kwargs={'pk': recipe_pk}))
