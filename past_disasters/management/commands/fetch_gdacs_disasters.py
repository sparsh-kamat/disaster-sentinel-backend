import xml.etree.ElementTree as ET
import requests
import time
from django.core.management.base import BaseCommand
from past_disasters.models import GdacsDisasterEvent
from unidecode import unidecode
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from django.utils.timezone import now

# GDACS RSS feed URL
GDACS_FEED_URL = "https://www.gdacs.org/xml/rss.xml"

# Namespace mappings
NS = {
    'geo': "http://www.w3.org/2003/01/geo/wgs84_pos#",
    'gdacs': "http://www.gdacs.org",
    'georss': "http://www.georss.org/georss",
}

# Map GDACS eventtype codes to full names
EVENT_TYPE_MAP = {
    'EQ': 'Earthquake',
    'FL': 'Flood',
    'TC': 'Tropical Cyclone',
    'VU': 'Volcano',
    'MP': 'Mass Movement',
    'SE': 'Severe Weather',
    'WF' : 'Wild Fire',
}

geolocator = Nominatim(user_agent="gdacs_disaster_app")

def send_alert(disaster_data):
    print(f"🚨 ALERT: {disaster_data['title']} | Level: {disaster_data['alertlevel']}")

def get_state_from_coordinates(lat, lon, retries=3):
    for attempt in range(retries):
        try:
            location = geolocator.reverse((lat, lon), exactly_one=True, language='en', timeout=10)
            if location and location.raw.get("address"):
                state = location.raw["address"].get("state") or location.raw["address"].get("region")
                if state:
                    if any(ord(c) > 127 for c in state):
                        return unidecode(state)
                    return state
        except (GeocoderTimedOut, GeocoderUnavailable) as geo_err:
            print(f"⏳ Geocoding retry {attempt+1}: {geo_err}")
            time.sleep(1.5)
        except Exception as e:
            print(f"❌ Unexpected geocoding error: {e}")
            break
    return None

def fetch_and_store_gdacs_disasters():
    try:
        response = requests.get(GDACS_FEED_URL)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except Exception as e:
        print(f"❌ Failed to fetch or parse GDACS RSS feed: {e}")
        return

    items = root.findall("./channel/item")
    if not items:
        print("⚠️ No disaster items found in feed.")
        return

    for item in items:
        try:
            eventid = item.findtext("gdacs:eventid", namespaces=NS)
            if not eventid:
                print("⚠️ Skipping item with no eventid.")
                continue

            if GdacsDisasterEvent.objects.filter(eventid=eventid).exists():
                print(f"🔁 Event {eventid} already exists. Skipping.")
                continue

            # Extract all fields
            eventtype_code = item.findtext("gdacs:eventtype", namespaces=NS) or ""
            eventtype_full = EVENT_TYPE_MAP.get(eventtype_code, eventtype_code)
            alertlevel = item.findtext("gdacs:alertlevel", namespaces=NS) or ""
            severity = item.findtext("gdacs:severity", namespaces=NS) or ""
            population = item.findtext("gdacs:population", namespaces=NS) or ""
            country = item.findtext("gdacs:country", namespaces=NS) or ""
            iso3 = item.findtext("gdacs:iso3", namespaces=NS) or ""

            # Set fromdate and todate to None (empty)
            fromdate = None
            todate = None

            iscurrent = item.findtext("gdacs:iscurrent", namespaces=NS) or "false"
            iscurrent = iscurrent.lower() == "true"

            if(iscurrent == 'false'):
                continue

            # Skip if no country
            if not country.strip():
                print(f"⏭️ Skipping event {eventid} because country is missing.")
                continue

            # Get coordinates
            lat_elem = item.find("{http://www.w3.org/2003/01/geo/wgs84_pos#}lat")
            lon_elem = item.find("{http://www.w3.org/2003/01/geo/wgs84_pos#}long")
            latitude = float(lat_elem.text) if lat_elem is not None and lat_elem.text else None
            longitude = float(lon_elem.text) if lon_elem is not None and lon_elem.text else None

            georss_point = item.findtext("georss:point", namespaces=NS)
            if georss_point:
                try:
                    lat, lon = map(float, georss_point.split())
                    latitude = lat
                    longitude = lon
                except (ValueError, AttributeError):
                    pass

            title = f"{eventtype_full} in {country}"
            description = item.findtext("description") or ""
            link = item.findtext("link") or ""

            # Always use current datetime for pubDate
            pubDate = now()

            # Get state from coordinates if available
            state = None
            if latitude is not None and longitude is not None:
                state = get_state_from_coordinates(latitude, longitude)
                time.sleep(1.1)  # Rate limiting for geocoding service

            if not iscurrent:
                print(f"⏭️ Skipping non-current event {eventid}")
                continue

            # Create the disaster event
            disaster = GdacsDisasterEvent(
                eventid=eventid,
                title=title,
                description=description,
                link=link,
                pubDate=pubDate,
                latitude=latitude,
                longitude=longitude,
                state=state,
                eventtype=eventtype_code,
                alertlevel=alertlevel,
                severity=severity,
                population=population,
                country=country,
                iso3=iso3,
                fromdate=fromdate,
                todate=todate,
                report_url=link,
                iscurrent=iscurrent
            )

            # Validate and save
            try:
                disaster.full_clean()
                disaster.save()
                print(f"✅ Stored event {eventid} ({title}, State: {state or 'N/A'})")

                if alertlevel.lower() in ("orange", "red"):
                    send_alert({
                        "eventid": eventid,
                        "title": title,
                        "alertlevel": alertlevel,
                        "severity": severity,
                        "population": population,
                        "state": state,
                        "latitude": latitude,
                        "longitude": longitude,
                        "link": link,
                    })

            except Exception as e:
                print(f"⚠️ Validation error for event {eventid}: {e}")

        except Exception as e:
            print(f"⚠️ Error processing event: {e}")
            import traceback
            traceback.print_exc()

    print("✅ Finished fetching and storing GDACS disasters.")

class Command(BaseCommand):
    help = "Fetch and store enriched GDACS disaster data from RSS feed"

    def handle(self, *args, **kwargs):
        fetch_and_store_gdacs_disasters()
