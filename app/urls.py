from django.contrib import admin
from django.urls import include,path,re_path
from . import views
from . import AJAX_views
from . import API_views

urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
   
    path('create_alert/', views.create_alert, name='create_alert'),
    re_path('update_alert/(?P<alert_id>\d+)/$', views.update_alert,name='update_alert'),
    
    path('authenticate/', views.authenticate, name='authenticate'),
    path('logout/', views.logout_view, name='logout_view'),

    path('search_instrument/',AJAX_views.search_instrument,name='search_instrument'),
    path('add_instrument_to_watchlist/',AJAX_views.add_instrument_to_watchlist,name='add_instrument_to_watchlist'),
    path('delete_instrument_from_watchlist/',AJAX_views.delete_instrument_from_watchlist,name='delete_instrument_from_watchlist'),
    path('search_indicator/',AJAX_views.search_indicator,name='search_indicator'),
    path('get_indicator/',AJAX_views.get_indicator,name='get_indicator'),

    path('save_alert/',AJAX_views.save_alert,name='save_alert'),
    path('update_alert/',AJAX_views.update_alert,name='update_alert'),
    path('delete_alert/',AJAX_views.delete_alert,name='delete_alert'),

    re_path('enable_alert/(?P<alert_id>\d+)/$',views.enable_alert,name='enable_alert'),
    re_path('disable_alert/(?P<alert_id>\d+)/$',views.disable_alert,name='disable_alert'),

    path('create_indicator_log/',AJAX_views.create_indicator_log,name='create_indicator_log'),
    path('get_indicator_log/',AJAX_views.get_indicator_log,name='get_indicator_log'),
    path('update_indicator_log/',AJAX_views.update_indicator_log,name='update_indicator_log'),
    path('get_available_lines/',AJAX_views.get_available_lines,name='get_available_lines'),

    path('delete_indicator_log/',AJAX_views.delete_indicator_log,name='delete_indicator_log'),
    path('get_alert_conditions/',AJAX_views.get_alert_conditions,name='get_alert_conditions'),

    path('get_alerts_test/',API_views.get_alerts,name='get_alerts_test'),
    path('get_candles/',API_views.get_candles,name='get_candles'),

]
