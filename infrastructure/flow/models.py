from django.db import models

from infrastructure.place.models import Space


class Flow(models.Model):
    name = models.CharField(max_length=120)
    space = models.ForeignKey(
        Space, on_delete=models.CASCADE, blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)
    has_definitions = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Flujos Conversacionales"
        verbose_name = "Flujo Conversacional"
        unique_together = ('name', 'space')


class CrateType(models.Model):
    name = models.CharField(max_length=120, primary_key=True)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.public_name})"

    class Meta:
        verbose_name_plural = "Tipos de Contenedor (campaña)"
        verbose_name = "Tipo de Contenedor (campaña)"


class Crate(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    crate_type = models.ForeignKey(CrateType, on_delete=models.CASCADE)
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    has_templates = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.crate_type.name})"

    class Meta:
        verbose_name_plural = "Contenedores (campañas)"
        verbose_name = "Contenedor (campaña)"
        unique_together = ('name', 'crate_type')
