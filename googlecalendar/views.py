from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
from google.auth.exceptions import GoogleAuthError
from rest_framework.permissions import IsAuthenticated
from google.oauth2.credentials import Credentials
from .models import GoogleCalendarToken
from google.auth.transport.requests import Request
import datetime
import pytz



# importing logger
from ordering.logger import get_logger

logger = get_logger("csv_download_logger")


GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")


from .utils import get_free_slots

class GoogleAuthInitView(APIView):

    '''
    Initializes the OAuth flow by generating a Google authorization URL.
    '''

    permission_classes = [IsAuthenticated]
    
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
                scopes=["https://www.googleapis.com/auth/calendar"],
                redirect_uri=GOOGLE_REDIRECT_URI
            )
            auth_url, _ = flow.authorization_url(prompt='consent')

            # request.session['state'] =  flow.oauth2session.state
            request.session['state'] = str(flow.oauth2session.state)

            
            return Response({"auth_url": auth_url})
        
        except Exception as e:
            logger.error(f"Failed to initiate Google OAuth: {str(e)}", exc_info=True)
            return Response({"error": "Failed to initiate Google OAuth."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Error fetching calendar events: {str(e)}", exc_info=True)
            return Response({"error": "Failed to fetch calendar events."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleAuthCallbackView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self,request):
        try:
                
          
            code = request.GET.get('code')


            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [GOOGLE_REDIRECT_URI]
                    }
                },
                scopes=["https://www.googleapis.com/auth/calendar"],
                redirect_uri=GOOGLE_REDIRECT_URI
            )
          
            flow.fetch_token(code=code)
 
            credentials = flow.credentials
       
            
            

            GoogleCalendarToken.objects.update_or_create(
                user=request.user,
                defaults={
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'scopes': ",".join(credentials.scopes),
                }
            )

            return Response({'message': 'Google Calendar authenticated'})
        except GoogleAuthError as gae:
            logger.error(f"Google auth error: {str(gae)}", exc_info=True)
            return Response({"error": "Google authentication failed."}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Error fetching calendar events: {str(e)}", exc_info=True)
            return Response({"error": "Failed to fetch calendar events."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GoogleCalendarEventsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):


        token_obj = GoogleCalendarToken.objects.get(user=request.user)
        creds = Credentials(
            token=token_obj.token,
            refresh_token=token_obj.refresh_token,
            token_uri=token_obj.token_uri,
            scopes=token_obj.scopes.split(',')
        )

        if not creds.valid and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Also update the new token in DB
            token_obj.token = creds.token
            token_obj.save()

        service = build('calendar', 'v3', credentials=creds)
        # events_result = service.events().list(calendarId='primary', maxResults=10).execute()
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
       

        return Response({"events":event_data})






class FetchFreeMeetingSlot(APIView):

    '''
    Fetch free time slots from the user's Google Calendar
    between the current time and a provided end date.
    '''

    def get(self, request):

        user = request.user
        logger.info(f"Fetching free meeting slots for user {user.username}")

        try:
            token_obj = GoogleCalendarToken.objects.get(user=user)

            creds = Credentials(
                token=token_obj.token,
                refresh_token=token_obj.refresh_token,
                token_uri=token_obj.token_uri,
                scopes=token_obj.scopes.split(',')
            )

            if not creds.valid and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_obj.token = creds.token
                token_obj.save()

            service = build('calendar', 'v3', credentials=creds)

            # Get user's calendar timezone
            calendar = service.calendars().get(calendarId='primary').execute()
            user_timezone = calendar.get('timeZone', 'UTC')
            tz = pytz.timezone(user_timezone)

            # let `end_date` from request
            end_date_str = request.data.get('end_date')  # Format: 'YYYY-MM-DD'
            if not end_date_str:
                return Response({"error": "end_date is required (YYYY-MM-DD)"}, status=400)

            try:
                # Convert now and end_date to datetime with timezone
                now = datetime.datetime.now(tz)
                end_datetime = tz.localize(datetime.datetime.strptime(end_date_str, "%Y-%m-%d"))
                # Set the end_datetime to the end of the day (23:59:59) for full day coverage
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            except ValueError:
                return Response({"error": "Invalid end_date format. Use YYYY-MM-DD."}, status=400)

            # Google API free/busy request body
            request_body = {
                "timeMin": now.isoformat(),
                "timeMax": end_datetime.isoformat(),
                "timeZone": user_timezone,
                "items": [{"id": "primary"}]
            }

            busy_data = service.freebusy().query(body=request_body).execute()
            busy_times = busy_data['calendars']['primary'].get('busy', [])

            # Calculate free slots
            free_slots = []
            current = now

            get_free_slots(busy_times,free_slots,current,end_datetime,tz)

        

            return Response({
                "status": True,
                "timezone": user_timezone,
                "message": "Available free time slots",
                "data": free_slots
            }, status=status.HTTP_200_OK)
        
        except GoogleAuthError as gae:
            logger.error(f"Google authentication error: {str(gae)}", exc_info=True)
            return Response({"error": "Google authentication failed."}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Error fetching calendar events: {str(e)}", exc_info=True)
            return Response({"error": "Failed to fetch calendar events."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


