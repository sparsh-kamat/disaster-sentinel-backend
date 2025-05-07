# gdacs_scraper/scraper.py
# It's good practice to keep the scraping logic separate

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def scrape_gdacs_event_data(event_url):
    """
    Scrapes event data from a given GDACS event URL.

    Args:
        event_url (str): The URL of the GDACS event page.

    Returns:
        dict: A dictionary containing scraped event summary, latest headlines,
              and database news updates. Returns an empty dict on failure.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(event_url, headers=headers, timeout=10) # Added timeout
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
    except requests.RequestException as e:
        print(f"Failed to fetch page: {event_url}. Error: {e}")
        return {"error": f"Failed to fetch page: {e}", "event_summary": {}, "latest_headlines": [], "db_news_updates": []} # Return structured error
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    event_summary_data = {}
    latest_headlines = []
    db_news_updates = []

    # 1. Event Summary
    try:
        event_summary_div = soup.find('div', id='alert_summary_left')
        if event_summary_div:
            table = event_summary_div.find('table', class_='summary')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) == 2:
                        key = cols[0].get_text(strip=True).replace(":", "")
                        value = cols[1].get_text(strip=True)
                        event_summary_data[key] = value
    except Exception as e:
        print(f"Error scraping event summary: {e}")
        # Optionally, add specific error info to the response
        event_summary_data["error"] = "Could not parse event summary."


    # 2. Latest Media Headlines
    # The original script had a section for "Latest Media Headlines" and then another loop
    # for news_boxes. It seems the second loop was intended to be part of it or a refinement.
    # I'll integrate the logic to avoid redundancy and use the slick-cloned exclusion.
    try:
        news_main_div = soup.find('div', id='news_main')
        if news_main_div:
            # Excludes duplicated slick clones which can appear in carousels
            news_boxes = news_main_div.select('div.news_box:not(.slick-cloned)')
            for box in news_boxes:
                title_tag = box.find('span', class_='news_title')
                text_tag = box.find('span', class_='news_text') # Used for summary
                
                headline = ""
                link = None
                summary = ""

                if title_tag:
                    a_tag = title_tag.find('a')
                    if a_tag:
                        headline = a_tag.get_text(strip=True)
                        if a_tag.has_attr('href'):
                            link = urljoin(event_url, a_tag['href'])
                    else: # Fallback if no <a> tag directly in title
                        headline = title_tag.get_text(strip=True)
                
                if text_tag:
                    summary = text_tag.get_text(separator=' ', strip=True)

                if headline: # Only add if a headline was found
                    latest_headlines.append({
                        "title": headline,
                        "link": link,
                        "summary": summary
                    })
    except Exception as e:
        print(f"Error scraping latest media headlines: {e}")
        # Optionally, add specific error info to the response

    # 3. Database News Updates
    try:
        db_news_div = soup.find('div', id='contentDBNews')
        if db_news_div:
            db_news_boxes = db_news_div.find_all('div', class_='news_box')
            for box in db_news_boxes:
                title_tag = box.find('span', class_='news_title')
                text_tag = box.find('span', class_='news_text')
                
                title = ""
                date_text = ""
                details = []

                if title_tag:
                    title = title_tag.get_text(strip=True)

                if text_tag:
                    # Date is usually the first text node before <br><br>
                    # Using .decode_contents() to preserve structure for splitting
                    text_content_html = text_tag.decode_contents()
                    
                    # Split by <br><br> or <br/> <br/> or <br> <br> (more robust)
                    parts = []
                    if "<br><br>" in text_content_html:
                        parts = text_content_html.split("<br><br>", 1)
                    elif "<br/><br/>" in text_content_html:
                        parts = text_content_html.split("<br/><br/>", 1)
                    elif "<br/> <br/>" in text_content_html:
                         parts = text_content_html.split("<br/> <br/>", 1)
                    elif "<br> <br>" in text_content_html:
                        parts = text_content_html.split("<br> <br>", 1)
                    else:
                        parts = [text_content_html]


                    if parts:
                        # The first part is assumed to be the date, clean it.
                        date_soup = BeautifulSoup(parts[0], 'html.parser')
                        date_text = date_soup.get_text(strip=True)
                    
                    # Parse the <ul> if available for details
                    ul = text_tag.find('ul')
                    if ul:
                        details = [li.get_text(strip=True) for li in ul.find_all('li')]
                    elif len(parts) > 1: # If no <ul>, maybe the second part of split is details
                        # This is a fallback, might need refinement based on actual content
                        detail_soup = BeautifulSoup(parts[1], 'html.parser')
                        # Attempt to get meaningful text, avoiding just re-adding the title if present
                        potential_details = detail_soup.get_text(separator='\n', strip=True)
                        if potential_details and potential_details.lower() != title.lower():
                             details = [line.strip() for line in potential_details.split('\n') if line.strip()]


                if title: # Only add if a title was found
                    db_news_updates.append({
                        "title": title,
                        "date": date_text,
                        "details": details
                    })
    except Exception as e:
        print(f"Error scraping database news updates: {e}")
        # Optionally, add specific error info to the response

    return {
        "event_summary": event_summary_data,
        "latest_headlines": latest_headlines,
        "db_news_updates": db_news_updates
    }

# --- Django specific files ---


# project_name/urls.py 
# (Your main project's urls.py)

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include the URLs from your app (e.g., gdacs_api_app)
    path('api/gdacs/', include('gdacs_api_app.urls')), 
]


# gdacs_api_app/urls.py 
# (Create this file in your app directory 'gdacs_api_app')

from django.urls import path
from .views import scrape_gdacs_view

urlpatterns = [
    # Defines the endpoint: /api/gdacs/scrape/?url=<GDACS_EVENT_URL>
    path('scrape/', scrape_gdacs_view, name='scrape_gdacs_event'),
]

# requirements.txt
# Add these to your project's requirements.txt file

# Django==x.y.z  (use your Django version)
# requests==2.31.0 (or latest)
# beautifulsoup4==4.12.3 (or latest)
