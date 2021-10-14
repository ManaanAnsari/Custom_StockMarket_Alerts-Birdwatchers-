from django.contrib import admin
from .models import *


# Register your models here.
admin.site.register(Candle)
admin.site.register(Instrument)
admin.site.register(Indicator)
admin.site.register(Indicator_log)
admin.site.register(Alerts)
admin.site.register(UserProfile)
