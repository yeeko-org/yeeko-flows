from django.contrib import admin

from infrastructure.persistent_media.models import Media
"""
class Media(models.Model):
    CHOICES_TYPE = (
        ('image', 'image'),
        ('video', 'video'),
        ('audio', 'audio'),
        ('file', 'file'),
        ('document', 'document'),
        ('sticker', 'sticker'),
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    file = models.FileField(upload_to='media/')
    media_type = models.CharField(max_length=20, choices=CHOICES_TYPE)
    name = models.CharField(max_length=100, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    media_id = models.CharField(max_length=100, blank=True, null=True)
    uploaded_media_id_at = models.DateTimeField(blank=True, null=True)
    expiration_days = models.IntegerField(default=30)
"""


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'media_type', 'name', 'uploaded_at',
                    'media_id', 'uploaded_media_id_at', 'expiration_days')
    search_fields = ('account', 'media_type', 'name', 'uploaded_at',
                     'media_id', 'uploaded_media_id_at', 'expiration_days')
    list_filter = ('account', 'media_type',
                   'uploaded_at', 'uploaded_media_id_at')
    readonly_fields = ('media_id', 'uploaded_media_id_at', 'uploaded_at')
    fieldsets = (
        (None, {
            'fields': ('account', 'file', 'media_type', 'name', 'uploaded_at')
        }),
        ('Media ID', {
            'fields': ('media_id', 'uploaded_media_id_at', 'expiration_days',)
        }),

    )
    ordering = ('uploaded_at', 'uploaded_media_id_at')
