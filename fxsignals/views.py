from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods

from .services import get_fx_data as fetch_fx_data
import json


@require_http_methods(["GET"])
def get_fx_data_view(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            fx_data = fetch_fx_data()
            html_table = fx_data.to_html(
                classes=["table", "table-striped"], border=0)
            return HttpResponse(html_table)
        except Exception as e:
            # You can adjust the error handling here as needed
            return HttpResponse(f"Error: {str(e)}", status=500)
    else:
        return HttpResponse("This request is not via AJAX.", status=400)


def home(request):
    context = {
        'name': 'Jun',
        # 'USD_JPY': jpy_dataframes['USD_JPY']
    }

    return render(request, 'dashboard.html', context)
