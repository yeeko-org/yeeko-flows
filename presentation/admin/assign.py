from django.contrib import admin
from infrastructure.assign.models import (
    ConditionRule,  Assign, ApplyBehavior, ParamValue
)


@admin.register(ConditionRule)
class ConditionRuleAdmin(admin.ModelAdmin):
    list_display = (
        'appear', 'fragment', 'reply', 'destination', 'extra', 'extra_exits',
    )
    search_fields = (
        'fragment__title', 'reply__title', 'destination__piece__name',
        'extra__name'
    )
    list_filter = (
        'appear', 'extra_exits', 'platforms', 'circles', 'roles'
    )
    raw_id_fields = (
        'fragment', 'reply', 'destination', 'extra', 'platforms', 'circles',
        'roles'
    )

    fieldsets = (
        ('General', {
            'fields': (
                'appear', 'fragment', 'reply', 'destination', 'extra',
                'extra_values', 'addl_params', 'extra_exits'
            )
        }),
        ('Relations', {'fields': ('platforms', 'circles', 'roles')}),
    )

    class Meta:
        verbose_name_plural = "Reglas de Condición"
        verbose_name = "Regla de Condición"


@admin.register(Assign)
class AssignAdmin(admin.ModelAdmin):
    list_display = (
        'extra', 'extra_value', 'is_remove', 'piece', 'reply', 'destination',
        'written', 'deleted'
    )
    search_fields = (
        'extra__name', 'piece__name', 'reply__title',
        'destination__piece__name', 'written__extra__name'
    )
    list_filter = ('is_remove', 'deleted')
    raw_id_fields = (
        'extra', 'circles', 'piece', 'reply', 'destination', 'written'
    )

    fieldsets = (
        ('General', {
            'fields': (
                'extra', 'extra_value', 'is_remove', 'piece', 'reply',
                'destination', 'written', 'deleted'
            )
        }),
        ('Circles and Extra Assignments', {'fields': ('circles',)}),
    )

    class Meta:
        verbose_name_plural = "Asignaciones"
        verbose_name = "Asignación"


class ParamValueInline(admin.TabularInline):
    model = ParamValue
    raw_id_fields = ('parameter', 'fragment', 'destination', 'piece', 'reply')
    extra = 0
    show_change_link = True


@admin.register(ApplyBehavior)
class ApplyBehaviorAdmin(admin.ModelAdmin):
    list_display = ('behavior', 'space', 'main_piece')
    search_fields = ('behavior__name', 'space__title', 'main_piece__name')
    raw_id_fields = ('behavior', 'space', 'main_piece')
    inlines = [ParamValueInline]

    class Meta:
        verbose_name_plural = "Aplicar Funciones"
        verbose_name = "Aplicar Función"


@admin.register(ParamValue)
class ParamValueAdmin(admin.ModelAdmin):
    list_display = (
        'parameter', 'apply_behavior', 'fragment', 'destination', 'piece',
        'reply', 'value'
    )
    search_fields = (
        'parameter__name', 'apply_behavior__behavior__name',
        'fragment__title', 'destination__piece__name', 'piece__name',
        'reply__title', 'value'
    )
    raw_id_fields = (
        'parameter', 'apply_behavior', 'fragment', 'destination', 'piece',
        'reply'
    )

    class Meta:
        verbose_name_plural = "Valores de Parámetros"
        verbose_name = "Valor de Parámetro"
