from django.db import models
from django.db.models import JSONField

from infrastructure.place.models import Space, Account
from infrastructure.users.models import User
from infrastructure.service.models import Platform


init_status = [
    ("chatbot", "Control de Chatbot"),
    ("human_agent", "Agente Humano"),
]


def default_params():
    return {}


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    public_name = models.CharField(max_length=50, blank=True, null=True)
    has_dashboard_access = models.BooleanField(default=False)
    is_tester = models.BooleanField(default=False)
    can_moderate = models.BooleanField(default=False)
    can_admin = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    order = models.IntegerField(
        blank=True, null=True, verbose_name="Orden de prioridad del rol"
    )

    def __str__(self):
        return self.public_name or self.name


class StatusAttendance(models.Model):
    name = models.CharField(max_length=80, primary_key=True)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    color = models.CharField(max_length=80, blank=True, null=True)
    icon = models.CharField(max_length=80, blank=True, null=True)
    show_in_tracking = models.BooleanField(
        default=False, verbose_name="Mostrar en seguimiento"
    )
    text_response = models.BooleanField(
        default=True, verbose_name="Respuesta de texto"
    )
    payload_response = models.BooleanField(
        default=True, verbose_name="Respuesta de payload"
    )

    def __str__(self):
        return f"{self.name} ({self.public_name})"

    class Meta:
        verbose_name_plural = "Status de Atención"
        verbose_name = "Status de Atención"


class Member(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    subscribed = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} ({self.space})"

    class Meta:
        verbose_name_plural = "Integrantes"
        verbose_name = "Integrante"


class MemberAccount(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    uid = models.CharField(
        max_length=191, blank=True, null=True
    )
    token = models.CharField(max_length=255, blank=True, null=True)
    config = JSONField(blank=True, null=True, default=default_params)
    last_interaction = models.DateTimeField(blank=True, null=True)
    status = models.ForeignKey(
        StatusAttendance, on_delete=models.CASCADE, blank=True, null=True,
        verbose_name="Status de Atención"
    )

    def __str__(self):
        return f"{self.member} - {self.account}"

    class Meta:
        verbose_name_plural = "Configuraciones de Member"
        verbose_name = "Configuración de Member"


class Chrono(models.Model):
    member_account = models.OneToOneField(
        MemberAccount, on_delete=models.CASCADE
    )
    checking_lapse = models.IntegerField(blank=True, null=True)
    last_notify = models.DateTimeField(blank=True, null=True)
    checking_date = models.DateTimeField(blank=True, null=True)
    interest_degree = models.IntegerField(default=60, blank=True)
    interest_current = models.IntegerField(default=60, blank=True)

    def __str__(self):
        return self.member_account

    class Meta:
        verbose_name_plural = "Cronos para notificaciones"
        verbose_name = "Crono para notificación"


class AuthConfig(models.Model):
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uid = models.CharField(
        max_length=100, blank=True, null=True
    )
    token = models.CharField(max_length=255, blank=True, null=True)
    config = JSONField(blank=True, null=True, default=default_params)

    def __str__(self):
        return f"{self.user} - {self.platform}"

    class Meta:
        verbose_name_plural = "Configuraciones de Autenticación"
        verbose_name = "Configuración de Autenticación"


class InviteExtension(models.Model):
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, blank=True, null=True
    )
    space = models.ForeignKey(
        Space, on_delete=models.CASCADE, blank=True, null=True
    )
    key = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=80, blank=True, null=True)
    last_name = models.CharField(max_length=80, blank=True, null=True)
    response = models.TextField(blank=True, null=True)
    date_invitation = models.DateTimeField(blank=True, null=True)
    date_accepted = models.DateTimeField(blank=True, null=True)
    inviter_user = models.ForeignKey(
        User, related_name="invitation", on_delete=models.CASCADE
    )
    viewed = models.DateTimeField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=300, blank=True, null=True)
    other_data = JSONField(blank=True, null=True)
    verified = models.BooleanField(null=True, default=None)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.member} - {self.space}"

    class Meta:
        verbose_name_plural = "Invitaciones a Espacios"
        verbose_name = "Invitación a Espacio"
