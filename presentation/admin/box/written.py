from django.contrib import admin
from infrastructure.box.models import Written
from presentation.admin.box.inline import AssignInline, DestinationInline


class AssignWriteInline(AssignInline):
    fk_name = 'written'


class DestinationWriteInline(DestinationInline):
    fk_name = 'written'


@admin.register(Written)
class WrittenAdmin(admin.ModelAdmin):
    list_display = ('id', 'extra', 'collection', 'available')
    search_fields = ('extra__name', 'collection__name')
    list_filter = ('available', 'extra', 'collection')
    raw_id_fields = ('extra', 'collection')
    inlines = [DestinationWriteInline, AssignWriteInline]

    fieldsets = (
        ('General', {
            'fields': ('extra', 'collection', 'available')
        }),
    )

    class Meta:
        verbose_name_plural = "Opciones escritas"
        verbose_name = "Opción escrita"
