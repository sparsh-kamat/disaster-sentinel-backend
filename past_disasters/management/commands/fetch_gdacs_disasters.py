# <your_app_name>/management/commands/fetch_gdacs_disasters.py

from lxml import etree as ET
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import time

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from past_disasters.models import GdacsDisasterEvent # Adjust import path

GDACS_FEED_URL = "https://www.gdacs.org/xml/rss.xml"
NS = { # Namespaces
    'geo': "http://www.w3.org/2003/01/geo/wgs84_pos#",
    'gdacs': "http://www.gdacs.org",
    'georss': "http://www.georss.org/georss",
    'dc': "http://purl.org/dc/elements/1.1/",
    'atom': "http://www.w3.org/2005/Atom"
}

def parse_gdacs_date(date_str):
    # (Keep the parse_gdacs_date function as defined previously)
    if not date_str: return None
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
    help = 'Fetches ALL disaster events (current and past) for India from GDACS RSS feed, determines state via geocoding (only if needed), and stores/updates events.' # <<< Modified help text

    geolocator = Nominatim(user_agent="disaster_sentinel_your_unique_app_identifier_for_nominatim")

    def add_arguments(self, parser):
         parser.add_argument('--no-geocode', action='store_true', help='Disable reverse geocoding.')
         parser.add_argument('--force-geocode', action='store_true', help='Force reverse geocoding.')

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
            parser = ET.XMLParser(recover=True)
            root = ET.fromstring(response.content, parser=parser)
        except ET.XMLSyntaxError as e:
            raise CommandError(f"Failed to parse XML feed: {e}")

        processed_count = 0
        created_count = 0
        updated_count = 0
        geocoded_count = 0
        skipped_geocode_count = 0
        # current_event_ids_in_feed = set() # Not needed if not marking old events separately

        items = root.xpath("./channel/item")
        self.stdout.write(f"Found {len(items)} items in feed.")

        for item in items:
            event_id = None
            try:
                data = self.extract_disaster_data(item)
                event_id = data.get('eventid')

                if not event_id:
                    self.stderr.write(self.style.WARNING("Skipping item with missing eventid."))
                    continue

                # --- Filter for India (RE-ENABLED) ---
                is_india = False # <<< RE-ENABLED
                country_str = data.get('country', '') # <<< RE-ENABLED
                iso3_str = data.get('iso3', '') # <<< RE-ENABLED
                if country_str and 'india' in country_str.lower(): is_india = True # <<< RE-ENABLED
                elif iso3_str and iso3_str.upper() == 'IND': is_india = True # <<< RE-ENABLED
                # --- End Re-enabled Block ---

                # --- ADDED Filter: Skip if not India ---
                if not is_india: # <<< ADDED THIS CHECK
                    continue # Skip non-India events
                # --- End Added Filter ---

                # --- iscurrent check remains commented out as we want past events too ---
                # if not data.get('iscurrent'):
                #    continue

                existing_obj = GdacsDisasterEvent.objects.filter(eventid=event_id).first()
                existing_state = existing_obj.state if existing_obj and existing_obj.state else None
                needs_geocoding = (not existing_state) or force_geocode

                disaster_state = existing_state
                perform_geocode = (
                    needs_geocoding and not disable_geocode and
                    data.get('latitude') is not None and data.get('longitude') is not None
                )

                if perform_geocode:
                    # (Geocoding logic remains the same)
                    try:
                        time.sleep(1.1)
                        location = self.geolocator.reverse(
                            (data['latitude'], data['longitude']),
                            exactly_one=True, language='en', timeout=10
                        )
                        if location and location.raw and 'address' in location.raw:
                            address = location.raw['address']
                            geocoded_state_value = address.get('state') or address.get('state_district')
                            if geocoded_state_value:
                                disaster_state = geocoded_state_value
                                geocoded_count += 1
                            else:
                                self.stdout.write(self.style.WARNING(f"  Geocoding found address but no state field for {event_id}"))
                        else:
                            self.stdout.write(self.style.WARNING(f"  No address details found via geocoding for {event_id}"))
                    except (GeocoderTimedOut, GeocoderServiceError) as geo_e:
                        self.stderr.write(self.style.ERROR(f"  Geocoding service error for {event_id}: {geo_e}"))
                    except Exception as geo_e_other:
                         self.stderr.write(self.style.ERROR(f"  Unexpected geocoding error for {event_id}: {geo_e_other}"))
                elif not disable_geocode and needs_geocoding:
                    self.stdout.write(self.style.WARNING(f"  Skipping geocoding for {event_id} due to missing coordinates."))
                elif not needs_geocoding:
                     skipped_geocode_count += 1

                # --- Prepare data for the model ---
                defaults = {
                    'title': data.get('title', 'N/A'),
                    'description': data.get('description'),
                    'link': data.get('link', ''),
                    'pubDate': parse_gdacs_date(data.get('pubDate')),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'state': disaster_state,
                    'eventtype': data.get('eventtype', 'Unknown'),
                    'alertlevel': data.get('alertlevel'),
                    'severity': data.get('severity'),
                    'population': data.get('population'),
                    'country': data.get('country'),
                    'iso3': data.get('iso3'),
                    'fromdate': parse_gdacs_date(data.get('fromdate')),
                    'todate': parse_gdacs_date(data.get('todate')),
                    'iscurrent': data.get('iscurrent', False), # Use value from feed
                }
                defaults = {k: v for k, v in defaults.items() if v is not None}

                # --- Use update_or_create ---
                obj, created = GdacsDisasterEvent.objects.update_or_create(
                    eventid=event_id, defaults=defaults
                )

                processed_count += 1 # Count all processed India events
                if created: created_count += 1
                else: updated_count += 1

            except Exception as e:
                title = item.xpath("string(./title)") or "Unknown Title"
                self.stderr.write(self.style.ERROR(f"Error processing item '{title}' (ID: {event_id}): {e}"))

        # --- Mark events no longer current (Block remains removed) ---

        # <<< CHANGE: Updated summary message back to India >>>
        self.stdout.write(self.style.SUCCESS(
            f"Finished processing feed. Processed {processed_count} India events found in feed. "
            f"Created: {created_count}, Updated: {updated_count}. "
            f"Geocoded state for {geocoded_count} events. "
            f"Skipped geocoding for {skipped_geocode_count} events (state already known)."
        ))

    # --- UPDATED extract_disaster_data using xpath ---
    def extract_disaster_data(self, item):
        # (Keep the extract_disaster_data function as defined previously)
        disaster = {}
        def get_text(path):
            results = item.xpath(f"./{path}/text()", namespaces=NS)
            return ' '.join(results).strip() if results else None
        def get_text_direct(path):
             result = item.xpath(f"string(./{path})", namespaces=NS)
             return result if result else None
        disaster["title"] = get_text_direct("title")
        disaster["description"] = get_text_direct("description")
        disaster["link"] = get_text_direct("link")
        disaster["pubDate"] = get_text_direct("pubDate")
        lat_text = get_text("geo:lat")
        lon_text = get_text("geo:long")
        try:
            disaster["latitude"] = float(lat_text) if lat_text else None
            disaster["longitude"] = float(lon_text) if lon_text else None
        except (ValueError, TypeError):
             disaster["latitude"] = None; disaster["longitude"] = None
        if disaster["latitude"] is None or disaster["longitude"] is None:
             georss_point = get_text("georss:point")
             if georss_point:
                 try:
                     coords = georss_point.split()
                     if len(coords) >= 2:
                         lat, lon = map(float, coords[:2])
                         disaster["latitude"] = lat; disaster["longitude"] = lon
                 except ValueError: pass
        disaster["eventtype"] = get_text_direct("gdacs:eventtype")
        disaster["alertlevel"] = get_text_direct("gdacs:alertlevel")
        disaster["severity"] = get_text_direct("gdacs:severity")
        disaster["population"] = get_text_direct("gdacs:population")
        disaster["country"] = get_text_direct("gdacs:country")
        disaster["eventid"] = get_text_direct("gdacs:eventid")
        disaster["cap"] = get_text_direct("gdacs:cap")
        disaster["icon"] = get_text_direct("gdacs:icon")
        disaster["iso3"] = get_text_direct("gdacs:iso3")
        disaster["fromdate"] = get_text_direct("gdacs:fromdate")
        disaster["todate"] = get_text_direct("gdacs:todate")
        is_current_text = get_text_direct("gdacs:iscurrent")
        disaster["iscurrent"] = bool(is_current_text and is_current_text.lower() == "true")
        return disaster
    # --- End UPDATED extract_disaster_data ---

