# gdacs_api_app/views.py 
# (Assuming you have a Django app named 'gdacs_api_app')

from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from .scraper import scrape_gdacs_event_data  # Import the scraping function from your scraper module
# from .scraper import scrape_gdacs_event_data # If scraper.py is in the same app directory
# For this example, let's assume scrape_gdacs_event_data is defined in this file or imported correctly.
# If you place the scraper function in a separate file like 'scraper.py' in the same app directory,
# use the import statement above. For simplicity in this combined example, I'll include it here.

# --- Paste the scrape_gdacs_event_data function here if not importing ---
# For brevity, I'm not pasting it again. Assume it's available in this scope.
# --- End of scraper function ---


@require_http_methods(["GET"]) # Only allow GET requests
def scrape_gdacs_view(request: HttpRequest):
    """
    API view to scrape GDACS event data.
    Expects a 'url' query parameter with the GDACS event URL.
    """
    event_url = request.GET.get('url')

    if not event_url:
        return JsonResponse({"error": "Missing 'url' query parameter"}, status=400)

    # Validate URL (basic check)
    if not event_url.startswith("https://www.gdacs.org/report.aspx"):
        return JsonResponse({"error": "Invalid GDACS URL format"}, status=400)

    try:
        # Call the scraping function
        data = scrape_gdacs_event_data(event_url)
        
        if data.get("error") and not (data["event_summary"] or data["latest_headlines"] or data["db_news_updates"]): # Check if only error is present
            return JsonResponse(data, status=500) # Internal server error if scraping failed fundamentally
        
        return JsonResponse(data, status=200)

    except Exception as e:
        # Catch any other unexpected errors during the process
        print(f"Unexpected error in scrape_gdacs_view: {e}")
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

