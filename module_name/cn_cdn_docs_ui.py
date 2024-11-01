"""
使用 CDN 加速 Swagger UI
"""

__all__ = (
    'replace_swagger_ui'
)

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi import applications


def replace_swagger_ui():
    def swagger_monkey_patch(*args, **kwargs):
        """
        Wrap the function which is generating the HTML for the /docs endpoint and
        overwrite the default values for the swagger js and css.
        """
        kwargs.pop('swagger_js_url', None)
        kwargs.pop('swagger_css_url', None)

        return get_swagger_ui_html(  # 以免中国大陆无法获取 js css, 以至无法加载页面
            *args, **kwargs,
            swagger_js_url="https://cdn.staticfile.org/swagger-ui/5.6.2/swagger-ui-bundle.min.js",
            swagger_css_url="https://cdn.staticfile.org/swagger-ui/5.6.2/swagger-ui.min.css"
        )

    # Actual monkey patch
    applications.get_swagger_ui_html = swagger_monkey_patch
