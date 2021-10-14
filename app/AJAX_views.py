
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from datetime import datetime    
from django.contrib.auth.decorators import login_required
from django.core import serializers
from .models import Instrument,UserProfile,Indicator,Candle,Indicator_log,Alerts
import json


@csrf_exempt
@login_required(login_url='/')
def search_instrument(request):
    # returns top 5 instrument based on search
    if request.method == "POST":
        context = {}
        search_term = request.POST.get('search_term')
        fetched_instruments = Instrument.objects.filter(name__contains = search_term.upper())[:5]
        context["status"] = "success"
        context["data"] = serializers.serialize("json", fetched_instruments)
        return JsonResponse(context)


@csrf_exempt
@login_required(login_url='/')
def search_indicator(request):
    # returns top 5 indicators based on search (longname or short name)
    if request.method == "POST":
        context = {}
        search_term = request.POST.get('search_term')
        # search term present in either long name or short name
        fetched_indicators = (Indicator.objects.filter(long_name__contains = search_term) | Indicator.objects.filter(short_name__contains = search_term))[:5]
        context["status"] = "success"
        context["data"] = serializers.serialize("json", fetched_indicators)
        return JsonResponse(context)


@csrf_exempt
@login_required(login_url='/')
def get_indicator(request):
    # returns details of indicator
    context = {}
    if request.method == "POST":
        ind_id = request.POST.get('indicator_id')
        if Indicator.objects.filter(pk = ind_id).exists():
            indicator = Indicator.objects.get(pk = ind_id)
            context["data"] = serializers.serialize("json", [indicator])
            context["status"] = "success"
            return JsonResponse(context)    
        context["status"] = "error"
        context["message"] = "indicator not found"
    return JsonResponse(context)


@csrf_exempt
@login_required(login_url='/')
def add_instrument_to_watchlist(request):
    # adds instruments to users personal watchlist
    context = {}
    if request.method == "POST":
        # get instrument id 
        instrument_id = request.POST.get('instrument_id')
        fetched_instruments = Instrument.objects.filter(pk = instrument_id)
        # if requested instrument exists
        if len(fetched_instruments):
            # get user profile to update watchlist
            user_profile = UserProfile.objects.get(user = request.user)
            # check if not instrument already present in watchlist
            if fetched_instruments[0] not in user_profile.watchlist.all():
                # add the instrument (many-to-many relationship)
                user_profile.watchlist.add(fetched_instruments[0])
                context["status"] = "success"
                context["data"] = serializers.serialize("json", fetched_instruments)
                return JsonResponse(context)
            context["status"] = "error"
            context["message"] = "already added"
            return JsonResponse(context)
        context["status"] = "error"
        context["message"] = "instrument not found"
        return JsonResponse(context)
    context["status"] = "error"
    context["message"] = "only post allowed"
    return JsonResponse(context)


@csrf_exempt
@login_required(login_url='/')
def delete_instrument_from_watchlist(request):
    # remove instrument from users watchlist
    context = {}
    if request.method == "POST":
        # get instrument id 
        instrument_id = request.POST.get('instrument_id')
        fetched_instruments = Instrument.objects.filter(pk = instrument_id)
        # if requested instrument exists
        if len(fetched_instruments):
            # get user profile to update watchlist
            user_profile = UserProfile.objects.get(user = request.user)
            # delete the instrument
            if fetched_instruments[0] in user_profile.watchlist.all():
                user_profile.watchlist.remove(fetched_instruments[0])
            context["status"] = "success"
            context["message"] = "instrument successfully removed"
            return JsonResponse(context)
        context["status"] = "error"
        context["message"] = "instrument not found"
        return JsonResponse(context)
    context["status"] = "error"
    context["message"] = "only post allowed"
    return JsonResponse(context)


@csrf_exempt
@login_required(login_url='/')
def save_alert(request):
    # todo make line from display lines
    context = {}
    if request.method == "POST":
        print(request.POST)
        alert_name = request.POST.get('alert_name')
        candle_id = request.POST.get('selected_candle')
        candle_obj = Candle.objects.get(pk=candle_id)
        # get all the indicator logs
        log_ids = request.POST.getlist('indicator_log_id')
        indicator_logs = Indicator_log.objects.filter(id__in = log_ids).filter(created_by=request.user)
        # store conditions
        alert_conditions = []
        # get condition 1
        cond1 = request.POST.get('selected_condition1')
        if cond1 != '':
            line1 = request.POST.get('selected_line1')
            line2 = request.POST.get('selected_line2')
            if line1 !='select' and line2 !='select':
                condition = []
                if line2 == 'value':
                    selected_value = request.POST.get('selected_value')
                    condition.append(line1)
                    condition.append(cond1)
                    condition.append(line2)
                    condition.append(selected_value)
                else:
                    condition.append(line1)
                    condition.append(cond1)
                    condition.append(line2)
                    
                alert_conditions.append(condition)
        # get condition 2
        cond2 = request.POST.get('selected_condition2')
        if cond2 != '':
            line3 = request.POST.get('selected_line3')
            line4 = request.POST.get('selected_line4')
            if line3 !='select' and line4 !='select':
                condition = []
                if line4 == 'value':
                    selected_value2 = request.POST.get('selected_value2')
                    condition.append(line3)
                    condition.append(cond2)
                    condition.append(line4)
                    condition.append(selected_value2)
                else:
                    condition.append(line3)
                    condition.append(cond2)
                    condition.append(line4)
                    
                alert_conditions.append(condition)
        
        # save alerts
        alert_conditions = json.dumps(alert_conditions)
        # alert message
        alert_message = request.POST.get('alert_message')
        alert_obj = Alerts(
            name=alert_name,
            candle = candle_obj,
            conditions_json = alert_conditions,
            created_by_profile = UserProfile.objects.get(user=request.user),
            message = alert_message
        )
        alert_obj.save()
        # add watchlist
        selected_instruments = request.POST.getlist('watchlist_select')
        instrument_objects = Instrument.objects.filter(id__in=selected_instruments) 
        for ins_obj in instrument_objects:
            alert_obj.applied_on.add(ins_obj)
        # add logs many to many
        for ind_log_obj in indicator_logs:
            alert_obj.indicator_log.add(ind_log_obj)

        context["status"] = "success"
        context["message"] = "successfully added"
    return JsonResponse(context)



@csrf_exempt
@login_required(login_url='/')
def update_alert(request):
    # todo make line from display lines
    context = {}
    if request.method == "POST":
        print(request.POST)
        alert_id = request.POST.get('alert_id')
        if Alerts.objects.filter(id=alert_id).exists():
            alert_obj = Alerts.objects.get(id=alert_id)
            alert_name = request.POST.get('alert_name')
            candle_id = request.POST.get('selected_candle')
            candle_obj = Candle.objects.get(pk=candle_id)
            # get all the indicator logs
            log_ids = request.POST.getlist('indicator_log_id')
            indicator_logs = Indicator_log.objects.filter(id__in = log_ids).filter(created_by=request.user)
            # store conditions
            alert_conditions = []
            # get condition 1
            cond1 = request.POST.get('selected_condition1')
            if cond1 != '':
                line1 = request.POST.get('selected_line1')
                line2 = request.POST.get('selected_line2')
                if line1 !='select' and line2 !='select':
                    condition = []
                    if line2 == 'value':
                        selected_value = request.POST.get('selected_value')
                        condition.append(line1)
                        condition.append(cond1)
                        condition.append(line2)
                        condition.append(selected_value)
                    else:
                        condition.append(line1)
                        condition.append(cond1)
                        condition.append(line2)
                        
                    alert_conditions.append(condition)
            # get condition 2
            cond2 = request.POST.get('selected_condition2')
            if cond2 != '':
                line3 = request.POST.get('selected_line3')
                line4 = request.POST.get('selected_line4')
                if line3 !='select' and line4 !='select':
                    condition = []
                    if line4 == 'value':
                        selected_value2 = request.POST.get('selected_value2')
                        condition.append(line3)
                        condition.append(cond2)
                        condition.append(line4)
                        condition.append(selected_value2)
                    else:
                        condition.append(line3)
                        condition.append(cond2)
                        condition.append(line4)
                        
                    alert_conditions.append(condition)
            
            alert_message = request.POST.get('alert_message')
            # save alerts
            alert_conditions = json.dumps(alert_conditions)
            alert_obj.name =alert_name
            alert_obj.candle = candle_obj
            alert_obj.conditions_json = alert_conditions
            alert_obj.message = alert_message
            alert_obj.save()
            # add watchlist
            selected_instruments = request.POST.getlist('watchlist_select')
            instrument_objects = Instrument.objects.filter(id__in=selected_instruments) 
            # remove older and fresh add
            alert_obj.applied_on.clear()
            for ins_obj in instrument_objects:
                alert_obj.applied_on.add(ins_obj)
            # add logs many to many
            # remove older and fresh add
            alert_obj.indicator_log.clear()
            for ind_log_obj in indicator_logs:
                alert_obj.indicator_log.add(ind_log_obj)
            # add message
            context["status"] = "success"
            context["message"] = "successfully updated"
    return JsonResponse(context)




@csrf_exempt
@login_required(login_url='/')
def delete_alert(request):
    # create temp row as log of indicator to store its value configuration
    context = {}
    if request.method == "POST":
        # get alert id
        alert_id = request.POST.get('alert_id')
        # if alert exists
        if Alerts.objects.filter(pk = alert_id).exists():
            # get alert object
            alert_obj = Alerts.objects.get(pk = alert_id)
            if UserProfile.objects.get(user=request.user) == alert_obj.created_by_profile:
                alert_obj.delete()
                context["status"] = "success"
                context["message"] = "alert successfully deleted"
                return JsonResponse(context)
            context["status"] = "error"
            context["message"] = "permission denied"
            return JsonResponse(context)
        context["status"] = "error"
        context["message"] = "Alert Not Found"
    return JsonResponse(context)



@csrf_exempt
@login_required(login_url='/')
def create_indicator_log(request):
    # create temp row as log of indicator to store its value configuration
    context = {}
    if request.method == "POST":
        # get indicator id
        ind_id = request.POST.get('indicator_id')
        # if indicator exists
        if Indicator.objects.filter(pk = ind_id).exists():
            # get indicator object
            indicator = Indicator.objects.get(pk = ind_id)
            # load its input variables and its default values
            default_input_dict = json.loads(indicator.line_default_inputs)
            # make display line eg:macd(12,26,9) used for frontend
            indicator_display_line = ','.join( str(v) for v in default_input_dict.values())
            indicator_display_line = indicator.short_name+"("+indicator_display_line+")"
            # create log object
            indicator_log_obj = Indicator_log(
                    indicator = indicator,
                    input_values = indicator.line_default_inputs,
                    created_by = request.user,
                    display_line = indicator_display_line
                )
            indicator_log_obj.save()
            # return
            context["indicator_display_line"] = indicator_display_line
            context["indicator_log_id"] = indicator_log_obj.id
            context["status"] = "success"
            return JsonResponse(context)    
        context["status"] = "error"
        context["message"] = "indicator not found"
    return JsonResponse(context)

@csrf_exempt
@login_required(login_url='/')
def delete_indicator_log(request):
    context = {}
    if request.method == "POST":
        # get indicator log id
        log_id = request.POST.get('indicator_log_id')
        # if log exists
        if Indicator_log.objects.filter(pk = log_id).exists():
            log_obj = Indicator_log.objects.get(pk = log_id)
            # created by current user
            if log_obj.created_by == request.user:
                log_obj.delete()
                context["status"] = "success"
                return  JsonResponse(context)
        context["status"] = "error"
        context["message"] = "some error occured"
    return  JsonResponse(context)


@csrf_exempt
@login_required(login_url='/')
def get_indicator_log(request):
    # get details of indicator value stored (log instead of javascript)
    context = {}
    if request.method == "POST":
        ind_id = request.POST.get('indicator_log_id')
        # if log exists
        if Indicator_log.objects.filter(pk = ind_id).exists():
            # return its values
            indicator_log_obj = Indicator_log.objects.get(pk = ind_id)
            context["indicator_log_values"] = indicator_log_obj.input_values
            context["status"] = "success"
            return JsonResponse(context)    
        context["status"] = "error"
        context["message"] = "indicator log not found"
    return JsonResponse(context)



@csrf_exempt
@login_required(login_url='/')
def update_indicator_log(request):
    # when value of an indicator is changed in frtontend update the values in log
    context = {}
    if request.method == "POST":
        # get id
        ind_id = request.POST.get('indicator_log_id')
        # if log exists
        if Indicator_log.objects.filter(pk = ind_id).exists():
            log_obj = Indicator_log.objects.get(pk = ind_id)
            # values json to be updated
            value_dict_to_store = {}
            ''' note : figure out a better logic here for now it works'''
            for key, value in request.POST.items():
                # skip the id part
                if key != "indicator_log_id":
                    if isinstance(value,list):
                        # if value is list
                        value_dict_to_store[key] = value[0]
                    else:
                        value_dict_to_store[key] = value
            
            # make display line eg:macd(12,26,9) used for frontend
            indicator_display_line = ','.join( str(v) for v in value_dict_to_store.values())
            indicator_display_line = log_obj.indicator.short_name+"("+indicator_display_line+")"

            # convert to json and store
            value_dict_to_store = json.dumps(value_dict_to_store)
            print(ind_id,request.POST,value_dict_to_store)
            log_obj.input_values = value_dict_to_store
            log_obj.display_line = indicator_display_line
            log_obj.save()
            context["indicator_display_line"] = indicator_display_line
            context["indicator_log_id"] = log_obj.id
            context["status"] = "success"
            return JsonResponse(context)
        context["status"] = "error"
        context["message"] = "indicator not found"
    return JsonResponse(context)



@csrf_exempt
@login_required(login_url='/')
def get_available_lines(request):
    # when value of an indicator is changed in frtontend update the values in log
    context = {}
    if request.method == "POST":
        display_lines = ["select","open","high","low","close"]
        log_ids = request.POST.getlist('indicator_log_id')
        indicator_logs = Indicator_log.objects.filter(id__in = log_ids)
        # print(default_lines,log_ids,indicator_logs)

        for log_obj in indicator_logs:
            inputs = json.loads(log_obj.input_values)
            indicator_display_line = ','.join( str(v) for v in inputs.values())
            indicator_display_line = log_obj.indicator.short_name+"("+indicator_display_line+")"
            display_lines.append(indicator_display_line)
            extra_lines = log_obj.indicator.extra_output_lines
            if (extra_lines is not None) and (extra_lines.strip() != "''"):
                extra_lines = extra_lines.split(',')
                display_lines = display_lines + extra_lines


        print(display_lines)
        context["status"] = "success"
        context["lines"] = display_lines
        return JsonResponse(context)
    return JsonResponse(context)



@csrf_exempt
@login_required(login_url='/')
def get_alert_conditions(request):
    # when value of an indicator is changed in frtontend update the values in log
    context = {}
    if request.method == "POST":
        alert_id = request.POST.get('alert_id')
        if Alerts.objects.filter(id = alert_id).exists():
            alert = Alerts.objects.get(id = alert_id)
            conditions = json.loads(alert.conditions_json)
            context["status"] = "success"
            context["conditions"] = conditions
            return JsonResponse(context)
    return JsonResponse(context)

