# <your_app_name>/management/commands/fetch_gdacs_disasters.py

from lxml import etree as ET
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import time # For potential sleep if rate limited

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction

# --- Geopy Imports ---
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
# --- End Geopy Imports ---

# Adjust import path for your model
from past_disasters.models import GdacsDisasterEvent # Assuming 'disasters' app

GDACS_FEED_URL = "https://www.gdacs.org/xml/rss.xml"
NS = { # Namespaces
    'geo': "http://www.w3.org/2003/01/geo/wgs84_pos#",
    'gdacs': "http://www.gdacs.org",
    # ... other namespaces if needed ...
}

def parse_gdacs_date(date_str):
    # (Keep the parse_gdacs_date function as defined previously)
    if not date_str:
        return None
    try:
        dt_naive = datetime.strptime(date_str.replace(' GMT', '+0000'), '%a, %d %b %Y %H:%M:%S %z')
        return dt_naive.astimezone(ZoneInfo("UTC"))
    except ValueError:
        try:
            dt_aware = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt_aware.astimezone(ZoneInfo("UTC"))
        except Exception as e_iso:
            print(f"Warning: Could not parse date '{date_str}': {e_iso}")
            return None

class Command(BaseCommand):
    help = 'Fetches current disaster events from GDACS RSS feed, determines state via geocoding (only if needed), and stores/updates India-specific events.'

    # --- Initialize Geolocator ---
    geolocator = Nominatim(user_agent="disaster_sentinel_your_unique_app_identifier_for_nominatim") # Replace with your unique ID

    def add_arguments(self, parser):
         parser.add_argument(
            '--no-geocode',
            action='store_true',
            help='Disable reverse geocoding to find state.',
        )
         parser.add_argument(
            '--force-geocode',
            action='store_true',
            help='Force reverse geocoding even if state exists in DB.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Fetching GDACS disaster feed...")
        disable_geocode = options['no_geocode']
        force_geocode = options['force_geocode']

        try:
            response = requests.get(GDACS_FEED_URL, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise CommandError(f"Failed to fetch GDACS feed: {e}")

        self.stdout.write("Parsing XML feed...")
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            raise CommandError(f"Failed to parse XML feed: {e}")

        processed_count = 0
        created_count = 0
        updated_count = 0
        geocoded_count = 0
        skipped_geocode_count = 0
        current_event_ids_in_feed = set()

        items = root.findall("./channel/item")
        self.stdout.write(f"Found {len(items)} items in feed.")

        for item in items:
            event_id = None # Initialize event_id for error reporting
            try:
                data = self.extract_disaster_data(item)
                event_id = data.get('eventid')

                if not event_id:
                    self.stderr.write(self.style.WARNING("Skipping item with missing eventid."))
                    continue

                if data.get('iscurrent'):
                    current_event_ids_in_feed.add(event_id)

                # --- Filter for India ---
                is_india = False
                country_str = data.get('country', '')
                iso3_str = data.get('iso3', '')
                if country_str and 'india' in country_str.lower():
                    is_india = True
                elif iso3_str and iso3_str.upper() == 'IND':
                    is_india = True

                if not is_india:
                    continue

                if not data.get('iscurrent'):
                    continue

                # --- OPTIMIZATION: Check if state needs geocoding ---
                existing_obj = GdacsDisasterEvent.objects.filter(eventid=event_id).first()
                existing_state = existing_obj.state if existing_obj and existing_obj.state else None
                needs_geocoding = (not existing_state) or force_geocode # Geocode if state is missing or forced

                disaster_state = existing_state # Start with existing state (or None)
                perform_geocode = (
                    needs_geocoding and
                    not disable_geocode and
                    data.get('latitude') is not None and
                    data.get('longitude') is not None
                )
                # --- End Optimization Check ---

                # --- Reverse Geocode to get State (Only if needed) ---
                if perform_geocode:
                    try:
                        # Respect Nominatim usage policy (max 1 req/sec)
                        time.sleep(1.1) # Sleep for slightly over 1 second
                        location = self.geolocator.reverse(
                            (data['latitude'], data['longitude']),
                            exactly_one=True,
                            language='en',
                            timeout=10
                        )
                        if location and location.raw and 'address' in location.raw:
                            address = location.raw['address']
                            geocoded_state_value = address.get('state')
                            if not geocoded_state_value: # Fallback
                                geocoded_state_value = address.get('state_district')

                            if geocoded_state_value:
                                disaster_state = geocoded_state_value # Update state with geocoded value
                                geocoded_count += 1
                                # self.stdout.write(f"  Geocoded state for {event_id}: {disaster_state}")
                            else:
                                # Geocoding succeeded but didn't return a state field
                                self.stdout.write(self.style.WARNING(f"  Geocoding found address but no state field for {event_id}"))
                        else:
                            self.stdout.write(self.style.WARNING(f"  No address details found via geocoding for {event_id}"))
                    except (GeocoderTimedOut, GeocoderServiceError) as geo_e:
                        self.stderr.write(self.style.ERROR(f"  Geocoding service error for {event_id}: {geo_e}"))
                    except Exception as geo_e_other:
                         self.stderr.write(self.style.ERROR(f"  Unexpected geocoding error for {event_id}: {geo_e_other}"))
                elif not disable_geocode and needs_geocoding:
                    # We needed geocoding but couldn't perform it (e.g., missing coords)
                    self.stdout.write(self.style.WARNING(f"  Skipping geocoding for {event_id} due to missing coordinates (state remains unknown)."))
                elif not needs_geocoding:
                     skipped_geocode_count += 1 # Count how many times we skipped


                # --- Prepare data for the model ---
                defaults = {
                    'title': data.get('title', 'N/A'),
                    'description': data.get('description'),
                    'link': data.get('link', ''),
                    'pubDate': parse_gdacs_date(data.get('pubDate')),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'state': disaster_state, # Use existing or newly geocoded state
                    'eventtype': data.get('eventtype', 'Unknown'),
                    'alertlevel': data.get('alertlevel'),
                    'severity': data.get('severity'),
                    'population': data.get('population'),
                    'country': data.get('country'),
                    'iso3': data.get('iso3'),
                    'fromdate': parse_gdacs_date(data.get('fromdate')),
                    'todate': parse_gdacs_date(data.get('todate')),
                    'iscurrent': True,
                }
                defaults = {k: v for k, v in defaults.items() if v is not None}

                # --- Use update_or_create ---
                obj, created = GdacsDisasterEvent.objects.update_or_create(
                    eventid=event_id,
                    defaults=defaults
                )

                processed_count += 1
                if created: created_count += 1
                else: updated_count += 1

            except Exception as e:
                title = item.findtext("title", default="Unknown Title")
                self.stderr.write(self.style.ERROR(f"Error processing item '{title}' (ID: {event_id}): {e}"))

        # --- Mark events no longer current ---
        num_updated_to_not_current = GdacsDisasterEvent.objects.filter(
            iscurrent=True, iso3='IND'
        ).exclude(
            eventid__in=current_event_ids_in_feed
        ).update(iscurrent=False, updated_at=timezone.now())

        if num_updated_to_not_current > 0:
             self.stdout.write(f"Marked {num_updated_to_not_current} previously current India event(s) as not current anymore.")

        self.stdout.write(self.style.SUCCESS(
            f"Finished processing feed. "
            f"Processed {processed_count} current India events. "
            f"Created: {created_count}, Updated: {updated_count}. "
            f"Geocoded state for {geocoded_count} events. "
            f"Skipped geocoding for {skipped_geocode_count} events (state already known)."
        ))

    def extract_disaster_data(self, item):
        # (Keep the extract_disaster_data function as defined previously)
        disaster = {}
        disaster["title"] = item.findtext("title")
        disaster["description"] = item.findtext("description")
        disaster["link"] = item.findtext("link")
        disaster["pubDate"] = item.findtext("pubDate") # Parse later

        lat_elem = item.find("geo:lat", NS)
        lon_elem = item.find("geo:long", NS)
        lat_text = lat_elem.text if lat_elem is not None else None
        lon_text = lon_elem.text if lon_elem is not None else None
        try:
            disaster["latitude"] = float(lat_text) if lat_text else None
            disaster["longitude"] = float(lon_text) if lon_text else None
        except (ValueError, TypeError):
             disaster["latitude"] = None
             disaster["longitude"] = None

        if disaster["latitude"] is None or disaster["longitude"] is None:
             georss_point = item.findtext("georss:point", namespaces=NS)
             if georss_point:
                 try:
                     lat, lon = map(float, georss_point.split())
                     disaster["latitude"] = lat
                     disaster["longitude"] = lon
                 except ValueError: pass

        disaster["eventtype"] = item.findtext("gdacs:eventtype", namespaces=NS)
        disaster["alertlevel"] = item.findtext("gdacs:alertlevel", namespaces=NS)
        disaster["severity"] = item.findtext("gdacs:severity", namespaces=NS)
        disaster["population"] = item.findtext("gdacs:population", namespaces=NS)
        disaster["country"] = item.findtext("gdacs:country", namespaces=NS)
        disaster["eventid"] = item.findtext("gdacs:eventid", namespaces=NS)
        disaster["cap"] = item.findtext("gdacs:cap", namespaces=NS)
        disaster["icon"] = item.findtext("gdacs:icon", namespaces=NS)
        disaster["iso3"] = item.findtext("gdacs:iso3", namespaces=NS)
        disaster["fromdate"] = item.findtext("gdacs:fromdate", namespaces=NS)
        disaster["todate"] = item.findtext("gdacs:todate", namespaces=NS)
        is_current_text = item.findtext("gdacs:iscurrent", namespaces=NS)
        disaster["iscurrent"] = bool(is_current_text and is_current_text.lower() == "true")

        return disaster
