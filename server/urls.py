"""
URL configuration for server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as static_serve

from apps.common.celery.flower import CeleryFlowerAPIView
from apps.common.core.utils import auto_register_app_url
from apps.common.swagger.views import JsonApi, Redoc, SwaggerUI
from apps.common.utils.media import media_serve

swagger_apis = [
    re_path("^api-docs/schema/", JsonApi.as_view(), name="schema"),
    path("api-docs/swagger/", SwaggerUI.as_view(url_name="schema"), name="swagger-ui"),
    path("api-docs/redoc/", Redoc.as_view(url_name="schema"), name="schema-redoc"),
]

urlpatterns = [
    re_path("^admin/", admin.site.urls),
    path("api/common/", include("apps.common.urls", namespace="common")),
    path("api/system/", include("apps.system.urls", namespace="system")),
    path("api/settings/", include("apps.settings.urls", namespace="settings")),
    path("api/notifications/", include("apps.notifications.urls", namespace="notifications")),
    path("api/virt_center/", include("apps.virt_center.urls", namespace="virt_center")),
    re_path("^api/flower/(?P<path>.*)$", CeleryFlowerAPIView.as_view(), name="flower-view"),
    # media路径配置 开发环境可以启动下面配置，正式环境需要让nginx读取资源，无需进行转发
    re_path("^media/(?P<path>.*)$", media_serve, {"document_root": settings.MEDIA_ROOT}),
    re_path("^api/static/(?P<path>.*)$", static_serve, {"document_root": settings.STATIC_ROOT}),
]

urlpatterns = swagger_apis + urlpatterns
auto_register_app_url(urlpatterns)
