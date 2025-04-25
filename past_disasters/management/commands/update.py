from django.core.management.base import BaseCommand
from past_disasters.models import GdacsDisasterEvent
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

class Command(BaseCommand):
    help = "Update state field in GdacsDisasterEvent using reverse geocoding"

    def handle(self, *args, **kwargs):
        geolocator = Nominatim(user_agent="gdacs_disaster_tracker")

        def reverse_geocode_state(lat, lon):
            try:
                location = geolocator.reverse((lat, lon), exactly_one=True, language='en')
                if location and location.raw and 'address' in location.raw:
                    return location.raw['address'].get('state')
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                print(f"⚠️ Geocoding failed (retrying later): {e}")
            except Exception as e:
                print(f"❌ Unexpected geocoding error: {e}")
            return None

        events = GdacsDisasterEvent.objects.filter(state__isnull=True).exclude(latitude__isnull=True).exclude(longitude__isnull=True)

        total = events.count()
        print(f"🔍 Found {total} events without state info.")

        for i, event in enumerate(events, start=1):
            print(f"🌐 ({i}/{total}) Processing: {event.eventid}")
            if event.latitude is None or event.longitude is None:
                print("❌ Missing coordinates. Skipping.")
                continue

            state = reverse_geocode_state(event.latitude, event.longitude)
            if state:
                event.state = state
                event.save(update_fields=['state'])
                print(f"✅ Updated event {event.eventid} with state: {state}")
            else:
                print(f"⚠️ Could not determine state for event {event.eventid}.")

            time.sleep(1)  # Respect Nominatim's rate limit
