# your_app/renderers.py
from rest_framework.renderers import JSONRenderer
from rest_framework import status

class GlobalJSONRenderer(JSONRenderer):
    """Wrap all responses in {status, message, data}."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response') if renderer_context else None
        status_code = response.status_code if response else None
        
        message = getattr(response, 'message', '')
        wrapped_data = data

        if isinstance(data, dict):
            if 'message' in data:
                message = data.pop('message')
            wrapped_data = data

        custom = {
            'status': status.is_success(status_code),
            'message': message,
            'data': wrapped_data
        }

        return super().render(custom, accepted_media_type, renderer_context)
