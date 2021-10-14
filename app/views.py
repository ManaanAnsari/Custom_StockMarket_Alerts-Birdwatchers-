
# django essentials
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render , HttpResponse,redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import logout,login
from django.contrib.auth.hashers import make_password
from datetime import datetime    
from django.contrib.auth.decorators import login_required
# telegram essentials
from django_telegram_login.widgets.constants import LARGE
from django_telegram_login.widgets.generator import create_callback_login_widget
from django_telegram_login.authentication import verify_telegram_authentication
# to send login/signup message 
from alerts.essentials.bot import send_telegram_message 
# database essentials
from .models import Instrument,UserProfile,Candle,Alerts
import json
from django.core import serializers

# global vars
bot_name = settings.TELEGRAM_BOT_NAME
bot_token = settings.TELEGRAM_BOT_TOKEN
redirect_url = settings.TELEGRAM_LOGIN_REDIRECT_URL


def index(request):
    # if alredy loggedin return to home page
    if request.user.is_authenticated:
        return redirect('/home')
    telegram_login_widget = create_callback_login_widget(bot_name, size=LARGE)
    context = {'telegram_login_widget': telegram_login_widget}
    return render(request,'index.html',context)


@csrf_exempt
def authenticate(request):
    # if alredy loggedin return to home page
    if request.user.is_authenticated:
        return redirect('/home')
    context = {}
    if request.method == "POST":
        # print(request.POST)
        # get all post variable
        telegram_user_id = request.POST.get('id')
        first_name = request.POST.get('first_name') if request.POST.get('first_name') is not None else 'force_filled_unknown'
        last_name = request.POST.get('last_name') if request.POST.get('last_name') is not None else 'force_filled_unknown'
        telegram_username = request.POST.get('username') if request.POST.get('username') is not None else 'force_filled_unknown'
        tele_hash = request.POST.get('hash')
        # print(telegram_user_id,first_name,last_name,telegram_username,tele_hash)
        print('checking if authenticated using telegram')
        # check if data from valid telegram source
        if verify_telegram_authentication(bot_token,request.POST):
            print('valid telegram user')
            # if user exist get its object
            if User.objects.filter(username=telegram_user_id).exists():
                user_obj = User.objects.get(username=telegram_user_id)
                # login the user
                login(request, user_obj)
                login_msg = "logged in on Birdwatchers web app"
                send_telegram_message([user_obj.username],[login_msg])
            else:
                # if user not exist create one
                user_obj = User(
                    username = telegram_user_id,
                    first_name = first_name,
                    last_name = last_name,
                    password = make_password(telegram_user_id),
                    is_superuser = 0,
                    is_staff = 0,
                    is_active = 1,
                    date_joined = datetime.now()
                )
                user_obj.save()
                user_profile_obj = UserProfile(
                    user = user_obj,
                    telegram_username = telegram_username
                )
                user_profile_obj.save()
                # login the user
                login(request, user_obj)
                signup_msg = "Thank you for signing up,\n you 'll recive all your alert messages here \n if you face any problem feel free to contact @ManaanAnsari "
                send_telegram_message([user_obj.username],[signup_msg])
            context["status"] = "success"
            context["message"] = "loggedin!"
            return JsonResponse(context)
        else:
            context["status"] = "error"
            context["message"] = "data not valid"
            return JsonResponse(context)
    context["status"] = "error"
    context["message"] = "post only"
    return JsonResponse(context)

@login_required(login_url='/')
def logout_view(request):
    logout(request)
    return redirect('/')

@login_required(login_url='/')
def home(request):
    context = {}
    user_profile = UserProfile.objects.get(user=request.user)
    context['user_profile'] = user_profile 
    context['alerts'] = Alerts.objects.filter(created_by_profile=user_profile)
    return render(request,'home.html',context=context)

@login_required(login_url='/')
def create_alert(request):
    context = {}
    user_profile = UserProfile.objects.get(user=request.user)
    context['user_profile'] = user_profile 
    context['candles'] = Candle.objects.all()
    return render(request,'create_alert.html',context=context)


@login_required(login_url='/')
def update_alert(request,alert_id):
    context = {}
    user_profile = UserProfile.objects.get(user=request.user)
    context['user_profile'] = user_profile 
    context['candles'] = Candle.objects.all()
    if Alerts.objects.filter(id=alert_id).exists():
        alert_obj = Alerts.objects.get(id=alert_id)
        if alert_obj.created_by_profile ==  user_profile:
            context['alert_details'] =  alert_obj
            context['alert_conditions'] =  json.loads(alert_obj.conditions_json)
            context['display_lines'] = get_display_lines_from_logs(alert_obj.indicator_log.all())
            print(context['display_lines'])
            context['condition_type'] =  {
                "":"select",
                "gt":"greater than",
                "lt":"less than",
                "xx":"corssing",
                "xx_up":"corssing up",
                "xx_down":"corssing down"
            }
    else:
        return redirect("/create_alert")
    return render(request,'update_alert.html',context=context)




@login_required(login_url='/')
def disable_alert(request,alert_id):
    # create temp row as log of indicator to store its value configuration
    # get alert id
    # if alert exists
    if Alerts.objects.filter(pk = alert_id).exists():
        # get alert object
        alert_obj = Alerts.objects.get(pk = alert_id)
        print(UserProfile.objects.get(user=request.user))
        print(alert_obj.created_by_profile)
        if UserProfile.objects.get(user=request.user) == alert_obj.created_by_profile:
            alert_obj.enabled = 0
            alert_obj.save()
    return redirect("/")


@login_required(login_url='/')
def enable_alert(request,alert_id):
    # create temp row as log of indicator to store its value configuration
    # get alert id
    # if alert exists
    if Alerts.objects.filter(pk = alert_id).exists():
        # get alert object
        alert_obj = Alerts.objects.get(pk = alert_id)
        if UserProfile.objects.get(user=request.user) == alert_obj.created_by_profile:
            alert_obj.enabled = 1
            alert_obj.save()
    return redirect("/")









def get_display_lines_from_logs(indicator_logs):
    # when value of an indicator is changed in frtontend update the values in log
    display_lines = {
        "select":"select",
        "open":"open",
        "high":"high",
        "low":"low",
        "close":"close",
    }
    for log_obj in indicator_logs:
        inputs = json.loads(log_obj.input_values)
        indicator_display_line = ','.join( str(v) for v in inputs.values())
        indicator_display_line = log_obj.indicator.short_name+"("+indicator_display_line+")"
        display_lines[indicator_display_line] = indicator_display_line
        extra_lines = log_obj.indicator.extra_output_lines
        if (extra_lines is not None) and (extra_lines.strip() != "''"):
            extra_lines = extra_lines.split(',')
            for line in extra_lines:
                display_lines[line] = line
    return display_lines




def  get_indicator_lines_from_logs(indicator_logs):
    indicator_lines = []
    indicator_display_lines = get_display_lines_from_logs(indicator_logs)
    for indicator_log in indicator_logs:
        if indicator_log.indicator.inputs_type == "line_based":
            # print(indicator_log.indicator.inputs_type)
            line_format = indicator_log.indicator.indicator_line_format
            line_format = line_format.split("_")
            line_vals_dict = json.loads(indicator_log.input_values)
            line_format_inputs = []
            for key in line_format:
                if key == "indicator":
                    line_format_inputs.append(indicator_log.indicator.short_name)
                else:
                    line_format_inputs.append(str(line_vals_dict[key]))
            line_format_inputs = '_'.join(line_format_inputs)
            indicator_lines.append({"line_name":line_format_inputs})

            indicator_display_line = ','.join( str(v) for v in line_vals_dict.values())
            indicator_display_line = indicator_log.indicator.short_name+"("+indicator_display_line+")"
            indicator_display_lines[indicator_display_line] = line_format_inputs
        
        elif indicator_log.indicator.inputs_type == "class_based":
            line_format = indicator_log.indicator.indicator_line_format
            class_vals_dict = json.loads(indicator_log.input_values)
            indicator_lines.append({
                "line_name":line_format,
                "values":class_vals_dict,
            })
            indicator_display_line = ','.join( str(v) for v in class_vals_dict.values())
            indicator_display_line = indicator_log.indicator.short_name+"("+indicator_display_line+")"
            indicator_display_lines[indicator_display_line] = line_format

    return indicator_lines,indicator_display_lines



def get_alerts_test(request,mins=None):
    alerts_to_return =[]
    if mins is not None:
        mins = str(mins)+'min'
    else:
        mins = '15min'
    
    candle = Candle.objects.get(name=mins)
    alerts = Alerts.objects.filter(candle= candle)
    if len(alerts):
        # all the alerts of this candel
        for alert in alerts:
            # make coditions here 
            alert_conditions = []
            # get logs ('ll be used to put values in format)
            indicator_logs = alert.indicator_log.all()
            # get all the indicators "text and its values"
            indicator_lines,display_lines = get_indicator_lines_from_logs(indicator_logs)
            # display_lines = get_display_lines_from_logs(indicator_logs)
            # print(indicator_lines,display_lines)
            # the conditions dtored in frontend format
            frontend_conditions = json.loads(alert.conditions_json)
            # loop through all the condition entered (max 2)
            for condition_details in frontend_conditions:
                condition = {}
                line1 = condition_details[0]
                cond = condition_details[1]
                line2 = condition_details[2]
                if line2 == 'value':
                    # get value ( add some validation here)
                    selected_value = condition_details[3]
                    # value crossover up or down
                    if cond == 'xx_up':
                        condition['value_crossover'] = [display_lines[line1],selected_value,'up']
                    elif cond == 'xx_down':
                        condition['value_crossover'] = [display_lines[line1],selected_value,'down']
                    # / above or below value
                    elif cond == 'gt':
                        condition['above_value'] = [display_lines[line1],selected_value]
                    elif cond == 'lt':
                        condition['below_value'] = [display_lines[line1],selected_value]
                else:
                    # line crossover up/down
                    if cond == 'xx_up':
                        condition['line_crossover'] = [display_lines[line1],display_lines[line2],'up']
                    elif cond == 'xx_down':
                        condition['line_crossover'] = [display_lines[line1],display_lines[line2],'down']
                    # above / below line
                    elif cond == 'gt':
                        condition['above_line'] = [display_lines[line1],display_lines[line2]]
                    elif cond == 'lt':
                        condition['below_line'] = [display_lines[line1],display_lines[line2]]
                alert_conditions.append(condition)
            watchlist = list(alert.applied_on.all().values_list('name', flat=True))
            tele_id = [alert.created_by_profile.user.username]
            print(indicator_lines,alert_conditions,watchlist,tele_id)
            alerts_to_return.append({
                'indicators' : indicator_lines,
                'alert_conditions':alert_conditions,
                'watchlist':watchlist,
                'tele_id':tele_id,
                'message': "testing "+alert.name,
            })
    print(get_candles())
    return JsonResponse(alerts_to_return,safe=False)

def get_candles():
    return list(Candle.objects.all().values_list('name', flat=True))



# # temp function 'll be replaced later by upload csv or something similar
# def add_instruments(request):
#     for z_id,name in instruments_dict.items():
#         instrument_obj = Instrument(
#             name=name,
#             zerodha_id = z_id
#         )
#         instrument_obj.save()
