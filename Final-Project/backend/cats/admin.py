from django.contrib import admin
from .models import Cat, CatPhoto, Vaccine, MedicalRecord, Favorite

admin.site.register(Cat)
admin.site.register(CatPhoto)
admin.site.register(Vaccine)
admin.site.register(MedicalRecord)
admin.site.register(Favorite)
