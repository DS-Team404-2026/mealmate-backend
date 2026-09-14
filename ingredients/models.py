# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Ingredients(models.Model):
    name = models.CharField(max_length=20, blank=True, null=True)
    category = models.CharField(max_length=20, blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    amount = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ingredients'


class RecipeBooks(models.Model):
    is_favorite = models.IntegerField(blank=True, null=True)
    preference = models.CharField(max_length=20, blank=True, null=True)
    saved_at = models.DateField(blank=True, null=True)
    fail_reason = models.CharField(max_length=4, blank=True, null=True)
    recipe = models.ForeignKey('Recipes', models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'recipe_books'


class RecipeFeedback(models.Model):
    like_dislike = models.IntegerField(blank=True, null=True)
    difficulty_result = models.IntegerField(blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    recommendations = models.ForeignKey('RecipeRecommendations', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'recipe_feedback'


class RecipeIngredients(models.Model):
    pk = models.CompositePrimaryKey('ingredient_id', 'recipe_id')
    ingredient = models.ForeignKey(Ingredients, models.DO_NOTHING)
    recipe = models.ForeignKey('Recipes', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'recipe_ingredients'


class RecipeRecommendations(models.Model):
    recommendation_type = models.IntegerField(blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    available_ingredients = models.CharField(max_length=255, blank=True, null=True)
    health_snapshot = models.CharField(max_length=255, blank=True, null=True)
    environment_snapshot = models.CharField(max_length=255, blank=True, null=True)
    prompt_text = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    recipe = models.ForeignKey('Recipes', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'recipe_recommendations'


class RecipeSteps(models.Model):
    step_order = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    recipe = models.ForeignKey('Recipes', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'recipe_steps'


class Recipes(models.Model):
    title = models.CharField(max_length=100, blank=True, null=True)
    difficulty = models.IntegerField(blank=True, null=True)
    cooking_time = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipes'


class UserEnvironments(models.Model):
    tools = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'user_environments'


class UserHealthProfiles(models.Model):
    blood_pressure = models.IntegerField(blank=True, null=True)
    diseases_id = models.IntegerField(blank=True, null=True)
    allergen = models.CharField(max_length=255, blank=True, null=True)
    diets = models.CharField(max_length=255, blank=True, null=True)
    profile = models.ForeignKey('UserProfiles', models.DO_NOTHING, blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_health_profiles'


class UserProfiles(models.Model):
    cooking_level = models.IntegerField(blank=True, null=True)
    housing = models.CharField(max_length=50, blank=True, null=True)
    preference = models.CharField(max_length=20, blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'user_profiles'


class UserRefrigerators(models.Model):
    quantity = models.IntegerField(blank=True, null=True)
    expired_at = models.DateField(blank=True, null=True)
    storage_type = models.CharField(max_length=20, blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    ingredient = models.ForeignKey(Ingredients, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'user_refrigerators'


class Users(models.Model):
    email = models.CharField(unique=True, max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    nickname = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
