from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
from google.auth.exceptions import GoogleAuthError

# importing logger
from ordering.logger import get_logger

logger = get_logger("csv_download_logger")


GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")

class GoogleAuthInitView(APIView):

    '''
    Initializes the OAuth flow by generating a Google authorization URL.
    '''
    
    def get(self, request):
        try:
        
            # Create OAuth flow using client config
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "redirect_uris": [GOOGLE_REDIRECT_URI],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                },
                scopes=["https://www.googleapis.com/auth/calendar.readonly"],
                redirect_uri=GOOGLE_REDIRECT_URI
            )
            auth_url, _ = flow.authorization_url(prompt='consent')
            return Response({"auth_url": auth_url})
        
        except Exception as e:
            logger.error(f"Failed to initiate Google OAuth: {str(e)}", exc_info=True)
            return Response({"error": "Failed to initiate Google OAuth."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        


class GoogleAuthCallbackView(APIView):

    '''
    Handles the callback from Google OAuth, exchanges code for access token,
    and fetches upcoming calendar events.
    '''
    def get(self, request):
        code = request.GET.get('code')
       
       
        if not code:
            return Response({"error": "No code provided"}, status=400)
        
        try:

            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET ,
                        "redirect_uris": [GOOGLE_REDIRECT_URI],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                },
                scopes=["https://www.googleapis.com/auth/calendar.readonly"],
                redirect_uri=GOOGLE_REDIRECT_URI
            )

            flow.fetch_token(code=code)
            credentials = flow.credentials
            

            # Build Google Calendar API client with authorized credentials
            service = build('calendar', 'v3', credentials=credentials)

            events_result = service.events().list(
                calendarId='primary',
                maxResults=5,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            event_data = [{
                'summary': e.get('summary'),
                'start': e['start'].get('dateTime'),
                'end': e['end'].get('dateTime'),
            } for e in events]

            return Response({"events": event_data})
        except GoogleAuthError as gae:
            logger.error(f"Google auth error: {str(gae)}", exc_info=True)
            return Response({"error": "Google authentication failed."}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            logger.error(f"Error fetching calendar events: {str(e)}", exc_info=True)
            return Response({"error": "Failed to fetch calendar events."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
