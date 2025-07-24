import requests
import os
from datetime import datetime, timezone

# --- API Endpoints ---
APOD_API_URL = "https://api.nasa.gov/planetary/apod"
PEOPLE_IN_SPACE_API_URL = "http://api.open-notify.org/astros.json"
ISS_LOCATION_API_URL = "http://api.open-notify.org/iss-now.json"

# --- GitHub Environment Variables ---
# Retrieve NASA API Key from GitHub Secrets.
# It's crucial this matches the secret name you set in GitHub.
NASA_API_KEY = os.getenv('NASA_API_KEY')
if not NASA_API_KEY:
    print("Error: NASA_API_KEY environment variable not set. Please configure it as a GitHub Secret.")
    # Exit or raise error if API key is critical and missing
    exit(1) # Exit if the key is not found, as APOD won't work without it.

def fetch_api_data(url, params=None, timeout=10):
    """Generic function to fetch data from an API."""
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def get_apod_content():
    """Fetches and formats Astronomy Picture of the Day data."""
    params = {"api_key": NASA_API_KEY}
    data = fetch_api_data(APOD_API_URL, params=params)

    if not data:
        return "Could not retrieve today's Astronomy Picture of the Day. Please check back later!"

    title = data.get("title", "No Title")
    explanation = data.get("explanation", "No explanation available.")
    date = data.get("date", "Unknown Date")

    # Handle video media type gracefully for embedding in README
    image_url = "https://via.placeholder.com/600x400.png?text=Image+Not+Available" # Default placeholder
    if data.get("media_type") == "video":
        # For videos, try to get a thumbnail or provide a generic video placeholder
        image_url = data.get("thumbnail_url", "https://via.placeholder.com/600x400.png?text=APOD+Video+Available")
        # You might also include the video URL for users to click
        video_link = f"[Watch Video]({data.get('url', '#')})"
        explanation += f"\n\n*Note: Today's APOD is a video. {video_link}*"
    else:
        image_url = data.get("hdurl", data.get("url", image_url)) # Prefer HD, fall back to default, then placeholder

    content = f""