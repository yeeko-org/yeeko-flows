from typing import TYPE_CHECKING

from django.db import models
from django.db.models import JSONField


from infrastructure.flow.models import Crate
from infrastructure.member.models.member import Member
from infrastructure.notification.models import Notification
from infrastructure.persistent_media.models import Media as PersistentMedia
from infrastructure.tool.models import Behavior, Collection
from infrastructure.xtra.models import Extra
from infrastructure.place.models import Account

if TYPE_CHECKING:
    from infrastructure.assign.models import Assign

MEDIA_TYPES = (
    ('image', 'Imagen'),
    ('video', 'Video'),
    ('audio', 'Audio'),
    ('file', 'Archivo'),
    ('sticker', 'Sticker'),
)


class AssignMixin:
    assignments: "models.QuerySet[Assign]"

    def set_assign(self, member, interaction):
        for assign in self.assignments.filter(deleted=False):
            assign.to_member(member, interaction)


class DestinationMixin:
    destinations: models.QuerySet["Destination"]

    def get_destinations(self):
        return self.destinations.filter(deleted=False).order_by('order')


class Written(models.Model, AssignMixin, DestinationMixin):
    extra = models.ForeignKey(
        Extra, on_delete=models.CASCADE,
        blank=True, null=True)
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE,
        blank=True, null=True)
    available = models.BooleanField(
        default=False, verbose_name='Disponible')

    def __str__(self):
        return self.extra.name if self.extra else str(self.pk)

    class Meta:
        verbose_name = 'Opción escrita'
        verbose_name_plural = 'Opciones escritas'


class Piece(models.Model, AssignMixin, DestinationMixin):
    TYPE_CHOICES = (
        ("content", "Contenido"),
        ("destinations", "Para Destinos"),
        ("template", "Template"),
    )
    piece_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='content')
    crate = models.ForeignKey(
        Crate, on_delete=models.CASCADE, related_name='pieces')
    name = models.CharField(
        max_length=80, verbose_name='Nombre')
    description = models.TextField(
        verbose_name='Descripción')
    behavior = models.ForeignKey(
        Behavior, on_delete=models.CASCADE,
        blank=True, null=True)
    default_extra = models.ForeignKey(
        Extra, on_delete=models.CASCADE,
        blank=True, null=True)
    insistent = models.BooleanField(
        default=False, verbose_name='Insistente')
    mandatory = models.BooleanField(
        default=False, verbose_name='Obligatorio')
    config = JSONField(blank=True, null=True, default=dict)
    written = models.OneToOneField(
        Written, on_delete=models.CASCADE,
        blank=True, null=True, verbose_name='Opción escrita')
    order_in_crate = models.SmallIntegerField(blank=True, null=True)
    deleted = models.BooleanField(
        default=False, verbose_name='Borrado')

    fragments: models.QuerySet["Fragment"]

    def __str__(self):
        return f"{self.name} ({self.crate.name})"

    class Meta:
        verbose_name = 'Pieza (Mensaje)'
        verbose_name_plural = 'Piezas (Mensajes)'
        ordering = ['order_in_crate']


class Fragment(models.Model):
    FRAGMENT_TYPES = (
        ("message", "Mensaje"),
        ("behavior", "Función Behavior"),
        ("embedded", "Pieza embebida"),
        ("media", "Persistent Multimedia")
    )
    fragment_type = models.CharField(
        max_length=20, choices=FRAGMENT_TYPES, blank=True, null=True
    )
    order = models.SmallIntegerField(default=0)

    piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, related_name='fragments')
    behavior = models.ForeignKey(
        Behavior, on_delete=models.CASCADE, blank=True, null=True)
    persistent_media = models.ForeignKey(
        PersistentMedia, on_delete=models.CASCADE, blank=True, null=True)

    addl_params = JSONField(blank=True, null=True)

    file = models.FileField(
        upload_to='box', blank=True, null=True,
        verbose_name='Archivo o imagen')
    media_url = models.CharField(
        max_length=255, verbose_name='URL de multimedia',
        blank=True, null=True)
    media_type = models.CharField(
        max_length=20, choices=MEDIA_TYPES, blank=True, null=True)

    header = models.CharField(
        max_length=255, verbose_name='Encabezado', blank=True, null=True)
    body = models.TextField(
        verbose_name='Texto', blank=True, null=True)
    footer = models.CharField(
        max_length=255, verbose_name='Pie de página', blank=True, null=True)
    reply_title = models.CharField(
        max_length=80, verbose_name='Título de botón de respuesta',
        blank=True, null=True)

    embedded_piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, blank=True, null=True,
        verbose_name='Pieza embebida')

    deleted = models.BooleanField(
        default=False, verbose_name='Borrado')

    # TODO Rick: Distinguir 'muchos botones' y 'pocos botones' // quick_replies
    replies: models.QuerySet["Reply"]

    def __str__(self):
        if self.fragment_type == 'message':
            return f"{self.piece.name} - {self.body}"
        elif self.fragment_type == 'behavior' and self.behavior:
            return f"{self.piece.name} - {self.behavior.name}"
        elif self.fragment_type == 'embedded' and self.embedded_piece:
            return f"{self.piece.name} - {self.embedded_piece.name}"
        elif self.fragment_type == 'media' and self.persistent_media:
            return f"{self.piece.name} - {self.persistent_media.get_name()}"
        return f"{self.piece.name} - {self.pk}"

    class Meta:
        verbose_name = 'Fragmento'
        verbose_name_plural = 'Fragmentos'
        ordering = ['order']


class Reply(models.Model, AssignMixin, DestinationMixin):
    # TODO Together: Qué implicación tiene esto? Cómo se determina?
    REPLY_TYPE_CHOICES = (
        ("payload", "Payload"),
        ("quick_reply", "Respuesta rápida"),
        ("url", "URL"),
    )

    reply_type = models.CharField(
        choices=REPLY_TYPE_CHOICES, max_length=20, default="payload")
    fragment = models.ForeignKey(
        Fragment, on_delete=models.CASCADE, related_name='replies')

    title = models.CharField(
        max_length=255, verbose_name='text', blank=True, null=True)
    is_header_section = models.BooleanField(default=False)
    description = models.CharField(
        max_length=255, verbose_name='Descripción', blank=True, null=True)
    large_title = models.CharField(
        max_length=255, verbose_name='Título grande', blank=True, null=True)
    addl_params = JSONField(blank=True, null=True)
    context = JSONField(
        blank=True, null=True, verbose_name='Contexto para chatGPT')
    order = models.SmallIntegerField(blank=True, null=True)
    is_jump = models.BooleanField(
        default=True, help_text='Funciona para evitar la pregunta')
    use_piece_config = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False, verbose_name='Borrado')

    def __str__(self):
        return f"{self.fragment} - {self.title}"

    class Meta:
        verbose_name = 'Respuesta (Botón)'
        verbose_name_plural = 'Respuestas (Botones)'
        ordering = ['order']


class MessageLink(models.Model, DestinationMixin):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    link = models.URLField(max_length=255, blank=True, null=True)
    message = models.CharField(max_length=140, blank=True, null=True)
    qr_code_png = models.ImageField(
        upload_to='qr_codes', blank=True, null=True)
    qr_code_svg = models.ImageField(
        upload_to='qr_codes', blank=True, null=True)

    def __str__(self):
        return f"{self.account} - {self.message}"

    class Meta:
        verbose_name_plural = "Message Links"
        verbose_name = "Message Link"


class Destination(models.Model, AssignMixin):
    DESTINATION_TYPES = (
        ('url', 'URL'),
        ('behavior', 'Función Behavior'),
        ('piece', 'Pieza'),
    )
    # --------------------------------origin--------------------------------
    reply = models.ForeignKey(
        Reply, on_delete=models.CASCADE, blank=True, null=True,
        related_name='destinations')
    written = models.ForeignKey(
        Written, on_delete=models.CASCADE, blank=True, null=True,
        verbose_name='Opción escrita', related_name='destinations')
    piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, blank=True, null=True,
        related_name='destinations')
    message_link = models.ForeignKey(
        MessageLink, on_delete=models.CASCADE, blank=True, null=True,
        verbose_name='Link con mensaje', related_name='destinations')
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, blank=True, null=True,
        related_name='destinations')
    # ------------------------------end origin------------------------------

    # -------------------------------destination----------------------------
    destination_type = models.CharField(
        max_length=20, choices=DESTINATION_TYPES,
        verbose_name='Tipo de destino')
    piece_dest = models.ForeignKey(
        Piece, on_delete=models.CASCADE, blank=True, null=True,
        related_name='origins')
    behavior = models.ForeignKey(
        Behavior, on_delete=models.CASCADE, blank=True, null=True,
        related_name='destinations')
    url = models.CharField(
        max_length=255, verbose_name='URL', blank=True, null=True)
    # -----------------------------end destination--------------------------

    addl_params = JSONField(blank=True, null=True)
    is_default = models.BooleanField(default=True)
    order = models.SmallIntegerField(blank=True, null=True)
    deleted = models.BooleanField(default=False, verbose_name='Borrado')

    def __str__(self):
        name = self.piece.name if self.piece else self.pk
        return f"{name} - {self.destination_type}"

    class Meta:
        verbose_name = 'Destino'
        verbose_name_plural = 'Destinos'
        ordering = ['order']

    def evalue_condition_rules(self, member: Member, platform_name: str):
        from infrastructure.assign.models import ConditionRule
        condition_rules = ConditionRule.objects.filter(destination=self)
        match_all = []
        match_any = []
        for condition_rule in condition_rules:
            evalue = condition_rule.evalue(member, platform_name)
            evalue = evalue if condition_rule.appear else not evalue
            if condition_rule.match_all_rules:
                match_all.append(evalue)
            else:
                match_any.append(evalue)

        if not match_all and not match_any:
            return True

        if match_all and match_any:
            return all(match_all) and any(match_any)

        if match_all:
            return all(match_all)

        if match_any:
            return any(match_any)


class PlatformTemplate(models.Model):
    STATUS_CHOICES = (
        ('APPROVED', 'Aprobado'),
        ('IN_APPEAL', 'En apelación'),
        ('PENDING', 'Pendiente'),
        ('REJECTED', 'Rechazado'),
        ('PENDING_DELETION', 'Pendiente de eliminación'),
        ('DELETED', 'Eliminado'),
        ('DISABLED', 'Desactivado'),
        ('PAUSED', 'Pausado'),
        ('LIMIT_EXCEEDED', 'Límite excedido'),
    )
    template_id = models.CharField(max_length=20)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    name = models.CharField(max_length=80)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING')
    category = models.CharField(max_length=80, blank=True, null=True)
    language = models.CharField(
        max_length=10, default='es_MX', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    raw_template = models.JSONField(default=dict)
    piece = models.OneToOneField(
        Piece, on_delete=models.CASCADE, blank=True, null=True,
        related_name='template')

    parameters: models.QuerySet["TemplateParameter"]

    def __str__(self):
        return f"{self.name} - {self.account}"


class TemplateParameter(models.Model):
    COMPONENT_CHOICES = (
        ("body", "Body"),
        ("header", "Header"),
        ("footer", "Footer"),
    )
    template = models.ForeignKey(
        PlatformTemplate, on_delete=models.CASCADE, related_name='parameters')
    component_type = models.CharField(
        max_length=10, choices=COMPONENT_CHOICES, default='body')
    key = models.CharField(max_length=80)
    order = models.SmallIntegerField(default=0)
    extra = models.ForeignKey(
        Extra, on_delete=models.CASCADE, blank=True, null=True)
    default_value = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.template} - {self.key}"
