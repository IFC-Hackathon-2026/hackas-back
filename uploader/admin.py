from django.contrib import admin

from uploader.models import Document, Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    search_fields = ('description', 'attachment_key', 'public_id')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    search_fields = ('description', 'attachment_key', 'public_id')
