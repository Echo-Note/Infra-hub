from django.apps import AppConfig


class VirtCenterConfig(AppConfig):
    """
    虚拟化中心
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.virt_center"
    verbose_name = "虚拟化中心"

    def ready(self):
        """应用准备就绪时导入信号处理器"""
        from . import signal_handlers  # noqa
