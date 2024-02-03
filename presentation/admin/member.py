from django.contrib import admin

from infrastructure.member.models import (
    AuthConfig, Chrono, InviteExtension, Member, MemberAccount,
    StatusAttendance
)


@admin.register(MemberAccount)
class MemberAccountAdmin(admin.ModelAdmin):
    list_display = ('member', 'account', 'uid', 'last_interaction', 'status')
    search_fields = (
        'member__name', 'account__title', 'uid', 'status__name',
        'member__user__email', 'member__user__first_name',
        'member__user__last_name', 'account__pid'
    )
    list_filter = ('status',)
    raw_id_fields = ('member', 'account')
    readonly_fields = ('last_interaction',)

    fieldsets = (
        (
            'General',
            {'fields': (
                'member', 'account', 'uid', 'token', 'config',
                'last_interaction', 'status'
            )
            }
        ),
    )

    class Meta:
        verbose_name_plural = "Configuraciones de Member"
        verbose_name = "Configuración de Member"


class MemberAccountInline(admin.StackedInline):
    model = MemberAccount
    raw_id_fields = ('account',)
    extra = 0
    show_change_link = True


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'space', 'active', 'role', 'created', 'subscribed', 'deleted'
    )
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name', 'space__title',
        'user__username', 'space__title', 'role__name'
    )
    list_filter = ('active', 'subscribed', 'deleted')
    raw_id_fields = ('user', 'space')
    readonly_fields = ('created',)
    inlines = [MemberAccountInline]

    fieldsets = (
        ('General', {
            'fields': ('user', 'space', 'active', 'role', 'created',
                       'subscribed', 'deleted')
        }),
    )

    class Meta:
        verbose_name_plural = "Integrantes"
        verbose_name = "Integrante"


@admin.register(StatusAttendance)
class StatusAttendanceAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_name', 'color', 'icon',
                    'show_in_tracking', 'text_response', 'payload_response')
    search_fields = ('name', 'public_name')
    list_filter = ('show_in_tracking', 'text_response', 'payload_response')

    fieldsets = (
        ('General', {
            'fields': ('name', 'public_name', 'color', 'icon')
        }),
        ('Tracking Settings', {
            'fields': ('show_in_tracking',)
        }),
        ('Response Settings', {
            'fields': ('text_response', 'payload_response')
        }),
    )

    class Meta:
        verbose_name_plural = "Status de Atención"
        verbose_name = "Status de Atención"


@admin.register(Chrono)
class ChronoAdmin(admin.ModelAdmin):
    list_display = ('member_account', 'checking_lapse', 'last_notify',
                    'checking_date', 'interest_degree', 'interest_current')
    search_fields = ('member_account__member__name',
                     'checking_lapse', 'interest_degree', 'interest_current')
    list_filter = ('checking_lapse',)
    raw_id_fields = ('member_account',)
    readonly_fields = ('last_notify', 'checking_date')

    fieldsets = (
        ('General', {
            'fields': ('member_account', 'checking_lapse', 'last_notify',
                       'checking_date')
        }),
        ('Interest Settings', {
            'fields': ('interest_degree', 'interest_current')
        }),
    )

    class Meta:
        verbose_name_plural = "Cronos para notificaciones"
        verbose_name = "Crono para notificación"


@admin.register(AuthConfig)
class AuthConfigAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'uid', 'token')
    search_fields = ('user__username', 'platform__public_name', 'uid')
    raw_id_fields = ('user', 'platform')

    fieldsets = (
        ('General', {
            'fields': ('user', 'platform', 'uid', 'token', 'config')
        }),
    )

    class Meta:
        verbose_name_plural = "Configuraciones de Autenticación"
        verbose_name = "Configuración de Autenticación"


@admin.register(InviteExtension)
class InviteExtensionAdmin(admin.ModelAdmin):
    list_display = ('member', 'space', 'key', 'inviter_user',
                    'date_invitation', 'date_accepted', 'verified')
    search_fields = (
        'member__user__username', 'space__title', 'key',
        'inviter_user__username', 'email', 'phone', 'gender')
    list_filter = ('date_invitation', 'date_accepted', 'verified')
    raw_id_fields = ('member', 'space', 'inviter_user')
    readonly_fields = ('viewed',)

    fieldsets = (
        ('General', {
            'fields': ('member', 'space', 'key', 'first_name', 'last_name',
                       'response')
        }),
        ('Dates', {
            'fields': ('date_invitation', 'date_accepted', 'viewed')
        }),
        ('Inviter', {
            'fields': ('inviter_user',)
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'gender')
        }),
        ('Other Data', {
            'fields': ('other_data',)
        }),
        ('Verification', {
            'fields': ('verified',)
        }),
        ('Role', {
            'fields': ('role',)
        }),
    )

    class Meta:
        verbose_name_plural = "Invitaciones a Espacios"
        verbose_name = "Invitación a Espacio"
