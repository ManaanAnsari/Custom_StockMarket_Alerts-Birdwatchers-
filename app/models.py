from django.db import models
from django.contrib.auth.models import User
# Create your models here.




class Instrument(models.Model):
    name = models.CharField(max_length=200)
    display_name = models.TextField(default=None,null=True)
    zerodha_id = models.CharField(max_length=200)
    source = models.CharField(max_length=200,default="NSE")
    created_at = models.DateTimeField(auto_now_add=True)
    
class Candle(models.Model):
    name = models.CharField(max_length=200)

class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    telegram_username = models.CharField( max_length=50 ,default=None,null=True)
    watchlist = models.ManyToManyField(Instrument)


class Indicator(models.Model):
    short_name = models.CharField(max_length=200)
    long_name = models.TextField(default=None,null=True)
    indicator_type = models.TextField(default=None,null=True)
    # sortoff like a requirement engin    
    indicator_line_format = models.TextField(default=None,null=True)
    line_default_inputs = models.TextField(default=None,null=True)
    inputs_type = models.TextField(default=None,null=True)
    extra_output_lines = models.TextField(default=None,null=True)
    class_input_variables = models.TextField(default=None,null=True)
    
# used to temp store (replacing javascript with this) 
class Indicator_log(models.Model):
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE)
    input_values =  models.TextField(default=None,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    # just to display on indicator table in create /update alert
    display_line = models.TextField(default=None,null=True)


class Alerts(models.Model):
    name = models.TextField(default=None,null=True)
    candle = models.ForeignKey(Candle, on_delete=models.CASCADE)
    conditions_json = models.TextField()
    applied_on = models.ManyToManyField(Instrument)
    message = models.TextField(default=None,null=True)
    created_by_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    enabled = models.CharField(max_length=10,default=1)
    indicator_log = models.ManyToManyField(Indicator_log)

class Notification_log(models.Model):
    alert = models.ForeignKey(Alerts, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)




