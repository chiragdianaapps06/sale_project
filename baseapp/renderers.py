# your_app/renderers.py
from rest_framework.renderers import JSONRenderer
from rest_framework import status

class GlobalJSONRenderer(JSONRenderer):
    """Wrap all responses in {status, message, data}."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response')
        status_code = response.status_code if response else None

        custom = {
            'status': status.is_success(status_code),
            'message': getattr(response, 'message', ''),
            'data': data
        }

        return super().render(custom, accepted_media_type, renderer_context)
