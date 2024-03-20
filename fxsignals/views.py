from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods

from .services import trend_signals, trend_heat_map
import json
import time


# @require_http_methods(["GET"])
# def get_fx_data_view(request):
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         try:
#             fx_data = fetch_fx_data()
#             html_table = fx_data.to_html(
#                 classes=["table", "table-striped"], border=0)
#             return HttpResponse(html_table)
#         except Exception as e:
#             return HttpResponse(f"Error: {str(e)}", status=500)
#     else:
#         return HttpResponse("This request is not via AJAX.", status=400)

@require_http_methods(["GET"])
def get_trend_signals(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            trend_data = trend_signals()
            html_table = trend_data.to_html(
                classes=["table", "table-striped", "text-center"], border=0)

            trend_heat_map(trend_data)

            return HttpResponse(html_table)
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=500)
    else:
        return HttpResponse("This request is not via AJAX.", status=400)


def home(request):
    context = {
        'name': 'Jun',
        'cache_buster': int(time.time()),
    }

    return render(request, 'dashboard.html', context)
