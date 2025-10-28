# -*- coding: utf-8 -*-
#
import ipaddress
import os

from django.conf import settings
from django.utils.translation import gettext_lazy as _

import geoip2.database
from geoip2.errors import GeoIP2Error

__all__ = ["get_ip_city_by_geoip"]
reader = None


def init_ip_reader():
    global reader
    if reader:
        return

    path = os.path.join(settings.DATA_DIR, "system", "GeoLite2-City.mmdb")
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), "GeoLite2-City.mmdb")
    if not os.path.exists(path):
        raise FileNotFoundError(f"IP Database not found, please run `python manage.py download_ip_db`")

    reader = geoip2.database.Reader(path)


def get_ip_city_by_geoip(ip):
    try:
        init_ip_reader()
    except Exception:
        return _("Unknown")

    try:
        is_private = ipaddress.ip_address(ip.strip()).is_private
        if is_private:
            return _("LAN")
    except ValueError:
        return _("Invalid ip")

    try:
        response = reader.city(ip)
    except GeoIP2Error:
        return _("Unknown")

    city_names = response.city.names or {}
    lang = settings.LANGUAGE_CODE[:2]
    if lang == "zh":
        lang = "zh-CN"
    city = city_names.get(lang, _("Unknown"))
    return city
