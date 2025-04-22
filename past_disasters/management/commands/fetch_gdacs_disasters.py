from gdacs.api import GDACSAPIReader
from past_disasters.models import GdacsDisasterEvent
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand
import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

def send_alert(disaster_data):
    print("Sending alert:", disaster_data)

def fetch_and_store_gdacs_disasters():
    reader = GDACSAPIReader()
    geojson_data = reader.latest_events()

    if hasattr(geojson_data, 'features'):
        events = geojson_data.features
    else:
        print("Error: GeoJSON object doesn't contain 'features'.")
        return

    for event in events:
        props = event['properties']
        event_id = props.get('eventid')
        event_type = props.get('eventtype', '')

        if not event_id:
            continue

        if GdacsDisasterEvent.objects.filter(eventid=event_id).exists():
            print(f"Event {event_id} already exists, skipping.")
            continue

        # Fetch enriched details using get_event
        try:
            print(f"Fetching details for Event ID: {event_id}, Event Type: {event_type}")
            detailed_event = reader.get_event(event_type=str(event_type), event_id=str(event_id))

            # ✅ Skip if not current
            iscurrent = detailed_event.get('gdacs:iscurrent', 'false').lower() == 'true'
            if not iscurrent:
                print(f"Skipping past disaster event {event_id} (not current).")
                continue

            # Extract coordinates
            latitude = float(detailed_event.get("geo:Point", {}).get("geo:lat", 0))
            longitude = float(detailed_event.get("geo:Point", {}).get("geo:long", 0))

            # Parse and clean fields
            title = detailed_event.get('title', props.get('name', ''))
            description = detailed_event.get('description', props.get('description', ''))
            link = detailed_event.get('link', props.get('url', {}).get('report', ''))
            pubDate = detailed_event.get('pubDate')
            fromdate = detailed_event.get('gdacs:fromdate')
            todate = detailed_event.get('gdacs:todate')
            alertlevel = detailed_event.get('gdacs:alertlevel', '')
            severity = detailed_event.get('gdacs:severity', {}).get('#text', '')
            population = detailed_event.get('gdacs:population', {}).get('#text', '')
            country = detailed_event.get('gdacs:country', '')
            iso3 = detailed_event.get('gdacs:iso3', '')
            state = None  # Optional reverse geocoding
            # image_url = detailed_event.get('enclosure', {}).get('@url') or None

            new_event = GdacsDisasterEvent.objects.create(
                eventid=event_id,
                title=title,
                description=description,
                link=link,
                pubDate=make_aware(datetime.datetime.strptime(pubDate, '%a, %d %b %Y %H:%M:%S %Z')) if pubDate else None,
                latitude=latitude,
                longitude=longitude,
                state=state,
                eventtype=event_type,
                alertlevel=alertlevel,
                severity=severity,
                population=population,
                country=country,
                iso3=iso3,
                fromdate=make_aware(datetime.datetime.strptime(fromdate, '%a, %d %b %Y %H:%M:%S %Z')) if fromdate else None,
                todate=make_aware(datetime.datetime.strptime(todate, '%a, %d %b %Y %H:%M:%S %Z')) if todate else None,
                report_url=link,
                # image_url=image_url,
                iscurrent=True
            )

            send_alert({
                "title": title,
                "eventtype": event_type,
                "latitude": latitude,
                "longitude": longitude,
                "alertlevel": alertlevel,
                "severity": severity,
                "population": population,
                "country": country,
                "state": state,
                "link": link,
                # "image_url": image_url
            })
        
        except Exception as e:
            logger.error(f"Error fetching event details for {event_id}: {e}")
            continue  # Skip this event and move to the next one

    print("✅ GDACS enriched disaster events fetch completed.")

class Command(BaseCommand):
    help = "Fetch and store enriched GDACS disaster data"

    def handle(self, *args, **kwargs):
        fetch_and_store_gdacs_disasters()
