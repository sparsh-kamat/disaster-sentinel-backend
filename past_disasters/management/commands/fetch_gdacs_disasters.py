from gdacs.api import GDACSAPIReader
from past_disasters.models import GdacsDisasterEvent
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand
import time
import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from django.utils.dateparse import parse_datetime as parse_date

def send_alert(disaster_data):
    print("Sending alert:", disaster_data)

import time
import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from gdacs.api import GDACSAPIReader
from past_disasters.models import GdacsDisasterEvent
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime as parse_date

geolocator = Nominatim(user_agent="gdacs_disaster_app")

def parse_date_safe(date_str):
    """Safely parse date string to timezone-aware datetime."""
    try:
        return make_aware(datetime.datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z'))
    except Exception as e:
        print(f"⚠️ Failed to parse date '{date_str}': {e}")
        return None

def get_state_from_coordinates(lat, lon, retries=3):
    """Get state name using reverse geocoding with retry and delay."""
    attempt = 0
    while attempt < retries:
        try:
            location = geolocator.reverse((lat, lon), exactly_one=True, language='en', timeout=10)
            if location and location.raw.get('address'):
                return location.raw['address'].get('state') or location.raw['address'].get('region')
        except (GeocoderTimedOut, GeocoderUnavailable) as geo_err:
            print(f"⏳ Reverse geocoding attempt {attempt+1} failed (timeout/unavailable): {geo_err}")
            time.sleep(1.5)  # wait before retry
        except Exception as e:
            print(f"❌ Unexpected geocoding error: {e}")
            break
        attempt += 1
    return None


def fetch_and_store_gdacs_disasters():
    reader = GDACSAPIReader()

    try:
        geojson_data = reader.latest_events()
    except Exception as e:
        print(f"❌ Failed to fetch GDACS events: {e}")
        return

    features = getattr(geojson_data, 'features', None)
    if not features:
        print("❌ No 'features' found in the fetched GDACS GeoJSON.")
        return

    for event in features:
        try:
            props = event.get('properties', {})
            event_id = props.get('eventid')
            event_type = props.get('eventtype', '')

            if not event_id:
                print("⚠️ Skipping event without 'eventid'.")
                continue

            if GdacsDisasterEvent.objects.filter(eventid=event_id).exists():
                # check if pubDate is already in the database and not null, if null then dont skip
                existing_event = GdacsDisasterEvent.objects.get(eventid=event_id)
                if existing_event.pubDate is  None:
                    # check if pubDate is  null
                    existing_event.pubDate = parse_date_safe(props.get('pubDate'))
                    existing_event.save()
                    print(f"✅ Updated pubDate for existing event {event_id}.")
                    continue
                    
                else:
                    # if pubDate is not null
                    print(f"ℹ️ Event {event_id} already exists, skipping.")
                    continue

            try:
                detailed_event = reader.get_event(event_type=str(event_type), event_id=str(event_id))
            except Exception as e:
                print(f"❌ Failed to fetch details for {event_id}: {e}")
                continue

            is_current = str(detailed_event.get('gdacs:iscurrent', 'false')).lower() == 'true'
            if not is_current:
                print(f"⏭️ Skipping non-current disaster event {event_id}.")
                continue

            geo_point = detailed_event.get("geo:Point", {})
            latitude = float(geo_point.get("geo:lat", 0) or 0)
            longitude = float(geo_point.get("geo:long", 0) or 0)

            title = props.get('name', '')
            description = props.get('description', '')
            link = props.get('url', {}).get('report', '')

            pub_date = parse_date(detailed_event.get('pubDate'))
            from_date = parse_date(detailed_event.get('gdacs:fromdate'))
            to_date = parse_date(detailed_event.get('gdacs:todate'))

            alertlevel = detailed_event.get('gdacs:alertlevel', '')
            severity = detailed_event.get('gdacs:severity', {}).get('#text', '')
            population = detailed_event.get('gdacs:population', {}).get('#text', '')
            country = detailed_event.get('gdacs:country', '')
            iso3 = detailed_event.get('gdacs:iso3', '')

            # 🧠 Fetch state safely
            state = get_state_from_coordinates(latitude, longitude)
            time.sleep(1.1)  # Respect Nominatim rate limit

            GdacsDisasterEvent.objects.create(
                eventid=event_id,
                title=title,
                description=description,
                link=link,
                pubDate=pub_date,
                latitude=latitude,
                longitude=longitude,
                state=state,
                eventtype=event_type,
                alertlevel=alertlevel,
                severity=severity,
                population=population,
                country=country,
                iso3=iso3,
                fromdate=from_date,
                todate=to_date,
                report_url=link,
                iscurrent=True
            )

            print(f"✅ Stored disaster event {event_id} ({state or 'No state'}).")

        except Exception as e:
            print(f"⚠️ Skipping problematic event due to error: {e}")
            continue

    print("✅ Completed fetching and storing GDACS events.")




class Command(BaseCommand):
    help = "Fetch and store enriched GDACS disaster data"

    def handle(self, *args, **kwargs):
        fetch_and_store_gdacs_disasters()
