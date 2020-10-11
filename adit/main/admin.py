from django.contrib import admin
from .models import AppSettings, DicomServer, DicomFolder

admin.site.site_header = "ADIT administration"


class DicomServerAdmin(admin.ModelAdmin):
    list_display = ("name", "ae_title", "host", "port")


admin.site.register(DicomServer, DicomServerAdmin)


class DicomFolderAdmin(admin.ModelAdmin):
    list_display = ("name", "path")


admin.site.register(DicomFolder, DicomFolderAdmin)


class AppSettingsAdmin(admin.ModelAdmin):
    pass


admin.site.register(AppSettings, AppSettingsAdmin)
