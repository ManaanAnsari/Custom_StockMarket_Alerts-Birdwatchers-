
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from datetime import datetime    
from django.contrib.auth.decorators import login_required
from django.core import serializers
from .models import Instrument,UserProfile,Indicator,Candle,Indicator_log,Alerts
import json


@csrf_exempt
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


@csrf_exempt
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
            
            indicator_display_line = ','.join( str(v) for v in class_vals_dict.values())
            indicator_display_line = indicator_log.indicator.short_name+"("+indicator_display_line+")"
            indicator_display_lines[indicator_display_line] = line_format
            
            class_variables = json.loads(indicator_log.indicator.class_input_variables)
            class_inputs_dict = {}
            for key,val in class_vals_dict.items():
                class_inputs_dict[class_variables[key]] = val

            indicator_lines.append({
                "line_name":line_format,
                "values":class_inputs_dict,
            })

    return indicator_lines,indicator_display_lines


@csrf_exempt
def get_alerts(request):
    alerts_to_return =[]
    mins = request.POST.get('candle')
    print(mins)
    # mins = '5min'
    if mins is None:
        return JsonResponse(alerts_to_return,safe=False)
    if not Candle.objects.filter(name=mins).exists():
        return JsonResponse(alerts_to_return,safe=False)
    candle = Candle.objects.get(name=mins)
    alerts = Alerts.objects.filter(candle= candle).filter(enabled=1)
    if len(alerts):
        # all the alerts of this candel
        for alert in alerts:
            try:
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
                        elif cond == 'xx':
                            condition['value_crossover'] = [display_lines[line1],selected_value,'any']
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
                        elif cond == 'xx':
                            condition['line_crossover'] = [display_lines[line1],display_lines[line2],'any']
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
                    # 'message': "testing {stock} {candle} "+alert.name,
                    'message': alert.message,
                })
            except Exception as e:
                print(e)
                print('some error in alert')
                continue
    return JsonResponse(alerts_to_return,safe=False)

@csrf_exempt
def get_candles(request):
    return JsonResponse(list(Candle.objects.all().values_list('name', flat=True)),safe=False)
