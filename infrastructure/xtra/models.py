from django.db import models
from django.db.models import JSONField

from infrastructure.place.models import default_params, Space
from infrastructure.flow.models import Flow


class ClassifyExtra(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    public_name = models.CharField(max_length=80, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    only_developers = models.BooleanField(default=False)
    user_visible = models.CharField(max_length=255, blank=True, null=True)
    is_public = models.BooleanField(default=False)
    order = models.IntegerField(default=8)
    icon = models.CharField(max_length=20, default="bookmark")
    pixel_excel = models.IntegerField(default=120)
    settings = JSONField(
        default=dict, verbose_name="Configuración adicional", blank=True, null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Clasificaciones de Extras"
        verbose_name = "Clasificación de Extras"
        ordering = ['order']


class Format(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    public_name = models.CharField(max_length=80, blank=True, null=True)
    javascript_name = models.CharField(max_length=50, blank=True, null=True)
    python_name = models.CharField(max_length=50, blank=True, null=True)
    params = JSONField(blank=True, null=True, default=default_params)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Formatos"
        verbose_name = "Formato"


class Extra(models.Model):
    name = models.CharField(max_length=80)
    classify = models.ForeignKey(ClassifyExtra, on_delete=models.CASCADE)
    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    flow = models.ForeignKey(
        Flow, on_delete=models.CASCADE, blank=True, null=True)
    format = models.ForeignKey(
        Format, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    has_session = models.BooleanField(default=False)
    params = JSONField(
        blank=True, null=True, default=default_params)
    controller = models.ForeignKey(
        'Extra', on_delete=models.CASCADE, blank=True, null=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.classify.name})"

    class Meta:
        verbose_name_plural = "Variables Extra"
        verbose_name = "Variable Extra"


class PresetValue(models.Model):
    extra = models.ForeignKey(Extra, on_delete=models.CASCADE)
    value = models.CharField(max_length=255, blank=True, null=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.extra.name} - {self.value}"

    class Meta:
        verbose_name_plural = "Valores Predefinidos de Extras"
        verbose_name = "Valor Predefinido de Extras"
