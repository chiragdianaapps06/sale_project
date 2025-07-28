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
from rest_framework.exceptions import ValidationError 

from django.contrib.auth import get_user_model

User = get_user_model()

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
            logger.error(f"Error fetching calendar events: {str(e)}", exc_info=True)
            return Response({"error": "Failed to fetch calendar events."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleAuthCallbackView(APIView):
    
    '''
    Authenticate Google Calendar and store credentials in DB
    '''

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
            # Fetch credentials using the authorization code
            logger.info(f"Fetching token with code: {code}")

            flow.fetch_token(code=code)
 
            credentials = flow.credentials
       
            
            

            data = GoogleCalendarToken.objects.update_or_create(
                user=request.user,
                defaults={
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'scopes': ",".join(credentials.scopes),
                }
            )

            return Response({'message': 'Google Calendar authenticated',"data":request.user.email})
        except GoogleAuthError as gae:
            logger.error(f"Google auth error: {str(gae)}", exc_info=True)
            return Response({"error": "Google authentication failed."}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Error occor while authentication: {str(e)}", exc_info=True)
            return Response({"error":"Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GoogleCalendarEventsView(APIView):

    '''
     Fetch Google Calendar events for authenticated user
    '''

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:

            # fetch user credential from database.
            token_obj = GoogleCalendarToken.objects.get(user=request.user)
            creds = Credentials(
                token=token_obj.token,
                refresh_token=token_obj.refresh_token,
                token_uri=token_obj.token_uri,
                scopes=token_obj.scopes.split(',')
            )

            # refresh token it expire
            if not creds.valid and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Also update the new token in DB
                token_obj.token = creds.token
                token_obj.save()
                logger.info("refreshed and updated in database.")
                
            # Initialize the Google Calendar API service
            service = build('calendar', 'v3', credentials=creds)
            logger.info("Google Calendar API service initialized.")
        
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
        

            return Response({"events":event_data},status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching calendar events: {str(e)}", exc_info=True)
            return Response({"error": "code is exprired (one time used) ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    





class FetchFreeMeetingSlot(APIView):

    '''
    Fetch Google Calendar events for authenticated user
    '''
    def get(self, request):
        user = request.user
        
        
        #  other_user_email be provided in the request body to get the availability for another user
        other_user_email = request.data.get('other_user_email')

        if not other_user_email:
            return Response({"error": "other_user_email is required."}, status=400)
        
        # Fetch the free slots for the current user
        current_user_free_slots = self.get_user_free_slots(request,user = user)

        # Fetch the free slots for the other user
        try:
            other_user_free_slots = self.get_user_free_slots(request,other_user_email=other_user_email)
        except GoogleCalendarToken.DoesNotExist:
            return Response({"error": f"No calendar token found for {other_user_email}"}, status=400)

        # Return the response with both free slots
        return Response({
            "status": True,
            "current_user_free_slots": current_user_free_slots,
            "other_user_free_slots": other_user_free_slots,
        }, status=status.HTTP_200_OK)

    def get_user_free_slots(self,request, user=None, other_user_email=None):
      
        '''
        This method is used to get free slots for a given user.
        It will either take the current user or an other user's email.
        '''

        if user:
            try:
                 # Get the Google Calendar Token of the user (current or other user)
                token_obj = GoogleCalendarToken.objects.get(user=user)
            except Exception as e:
                raise ValidationError("Current user does not have a valid token.")
                
        elif other_user_email:


            try:
                user_instance = User.objects.get(email=other_user_email)
                token_obj = GoogleCalendarToken.objects.get(user=user_instance)

            except User.DoesNotExist :
                raise ValidationError(f"No user found with email : {other_user_email}.")
            
            except GoogleCalendarToken.DoesNotExist:
                raise ValidationError(f"No calendar token found for user : {other_user_email}.")
            
            
        else:
            raise ValueError("Either user or other_user_email must be provided.")

        creds = Credentials(
            token=token_obj.token,
            refresh_token=token_obj.refresh_token,
            token_uri=token_obj.token_uri,
            scopes=token_obj.scopes.split(',')
        )

        # Refresh token if expired
        if not creds.valid and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_obj.token = creds.token
            token_obj.save()

        service = build('calendar', 'v3', credentials=creds)

        # Get user's calendar timezone
        calendar = service.calendars().get(calendarId='primary').execute()
        user_timezone = calendar.get('timeZone', 'UTC')
        tz = pytz.timezone(user_timezone)

        # Get `end_date` from the request
        end_date_str = request.data.get('end_date')  # Format: 'YYYY-MM-DD'
        if not end_date_str:
            raise ValueError("end_date is required (YYYY-MM-DD)")

        try:
            # Convert current time and end_date to datetime with timezone
            now = datetime.datetime.now(tz)
            end_datetime = tz.localize(datetime.datetime.strptime(end_date_str, "%Y-%m-%d"))

            # Set the end_datetime to the end of the day (23:59:59) for full day coverage
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
        except ValueError:
            raise ValueError("Invalid end_date format. Use YYYY-MM-DD.")

        # Preparing Google API free/busy request body
        request_body = {
            "timeMin": now.isoformat(),
            "timeMax": end_datetime.isoformat(),
            "timeZone": user_timezone,
            "items": [{"id": "primary"}]
        }

        busy_data = service.freebusy().query(body=request_body).execute()
        busy_times = busy_data['calendars']['primary'].get('busy', [])

        # Calculate free slots using a helper function
        free_slots = self.get_busy_slot(busy_times, now, end_datetime, tz)
        return free_slots

    def get_busy_slot(self, busy_times, current, end_datetime, tz):

        """
        Helper function to calculate free slots from busy times.
        """
        free_slots = []

        # Loop through the busy times and find gaps (free slots)
        for slot in busy_times:
            busy_start = datetime.datetime.fromisoformat(slot['start']).astimezone(tz)
            busy_end = datetime.datetime.fromisoformat(slot['end']).astimezone(tz)

            # If the current time is less than the busy slot start, we have a free slot
            if current < busy_start:
                free_slots.append({
                    "start": current.isoformat(),
                    "end": busy_start.isoformat()
                })
            current = max(current, busy_end)

        # Add final free slot if there's time left after the last busy period
        if current < end_datetime:
            free_slots.append({
                "start": current.isoformat(),
                "end": end_datetime.isoformat()
            })

        return free_slots



class GoogleScheduleMeetingView(APIView):

    '''
    Schedule a meeting between two users by checking availability in Google Calendar.
    '''
    permission_classes = [IsAuthenticated]

    def post(self, request):

        user = request.user
        start_time = request.data.get("start_time")
        end_time = request.data.get("end_time")
        other_user_email = request.data.get("other_user_email")
        summary = request.data.get("summary", "Meeting")
        description = request.data.get("description", "")

        if not all([start_time, end_time, other_user_email]):
            logger.error(f"Missing required fields. start_time: {start_time}, end_time: {end_time}, other_user_email: {other_user_email}")
            return Response({"error": "Missing required fields"}, status=400)

        try:
            token_obj = GoogleCalendarToken.objects.get(user=user)
        except GoogleCalendarToken.DoesNotExist:
            logger.error("Google token not found for the login user.")
            return Response({"error": "Google token not found for user"}, status=400)
        

        # Validate the other user's email
        if other_user_email:
            try:
                User.objects.get(email = other_user_email)
            except User.DoesNotExist:
                logger.error(f"No user found with with email L {other_user_email}.")
                raise ValidationError(f"No user found with email : {other_user_email}.")

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

        try:
            service = build("calendar", "v3", credentials=creds)

            request_body = {
                "timeMin": start_time,
                "timeMax": end_time,
                "items": [
                    {"id": "primary"},  # current user
                    {"id": other_user_email}  # other user
                ]
            }

            free_busy = service.freebusy().query(body=request_body).execute()
            calendars = free_busy.get("calendars", {})

            current_user_busy = calendars.get("primary", {}).get("busy", [])
            other_user_busy = calendars.get(other_user_email, {}).get("busy", [])
            print("Calendars:", other_user_busy )
            if current_user_busy:
                logger.warning(f"{current_user_busy} is busy in the selected slot.")
                return Response({
                    "status": False,
                    "message": "Current user is busy in selected slot"
                })

            if other_user_busy:
                logger.warning(f"{other_user_email} is busy in the selected slot.")
                return Response({
                    "status": False,
                    "message": f"{other_user_email} is busy in selected slot"
                })

           # Create the event if both users are free
            event_body = {
                "summary": summary,
                "description": description,
                "start": {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
                "end": {"dateTime": end_time, "timeZone": "Asia/Kolkata"},
                "attendees": [{"email": other_user_email}]
            }

            event = service.events().insert(calendarId='primary', body=event_body,sendUpdates='all').execute()
            logger.info(f"Meeting scheduled successfully between {user.email} and {other_user_email}. Event ID: {event.get('id')}")
            return Response({
                "status": True,
                "message": "Meeting scheduled successfully",
                "event": event
            })

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error: {str(e)}"
            }, status=500)


    