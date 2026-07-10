from django.contrib import admin
from .models import Cat, Vaccine, MedicalRecord, Favorite

admin.site.register(Cat)
admin.site.register(Vaccine)
admin.site.register(MedicalRecord)
admin.site.register(Favorite)