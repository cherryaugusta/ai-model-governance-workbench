import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def live(request):
    return JsonResponse({"status": "ok"})


def ready(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ready"})


def deps(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")

    redis.from_url(settings.REDIS_URL).ping()

    return JsonResponse({"status": "ok", "db": "ok", "redis": "ok"})