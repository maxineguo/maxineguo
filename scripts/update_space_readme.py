import requests
import os
from datetime import datetime, timezone

# --- API Endpoints ---
# These are the URLs for the APIs we'll be fetching data from.
APOD_API_URL = "https://api.nasa.gov/planetary/apod"
PEOPLE_IN_SPACE_API_URL = "http://api.open-notify.org/astros.json"
ISS_LOCATION_API_URL = "http://api.open-notify.org/iss-now.json"

# --- Configuration for NASA API Key ---
# We retrieve the NASA API Key from environment variables.
# When running on GitHub Actions, it will get this from the GitHub Secret.
# For local testing, you would set it in your terminal (see Phase 2, Step 4).
NASA_API_KEY = os.getenv('NASA_API_KEY')

# Basic check to ensure the API key is present.
# If not found, it prints an error and exits, preventing script failure on deployment.
if not NASA_API_KEY:
    print("ERROR: NASA_API_KEY environment variable not found.")
    print("Please ensure it's set as a GitHub Secret (NASA_API_KEY) in your repository settings.")
    print("For local testing, set it in your terminal: export NASA_API_KEY='YOUR_KEY'")
    exit(1) # Exits the script with an error code

def fetch_api_data(url, params=None, timeout=15):
    """
    Generic function to safely fetch JSON data from a given URL.
    Includes error handling for network issues and bad HTTP responses.
    Args:
        url (str): The API endpoint URL.
        params (dict, optional): Dictionary of query parameters. Defaults to None.
        timeout (int): Seconds to wait for a response before timing out.
    Returns:
        dict or None: The JSON response data if successful, None otherwise.
    """
    try:
        # Send a GET request to the specified URL with parameters and a timeout.
        response = requests.get(url, params=params, timeout=timeout)
        
        # Raise an HTTPError for bad responses (4xx or 5xx status codes).
        # This makes error handling cleaner.
        response.raise_for_status() 
        
        # Return the JSON parsed response.
        return response.json()
    except requests.exceptions.Timeout:
        print(f"ERROR: Request to {url} timed out after {timeout} seconds.")
        return None
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to {url}. Check internet connection or API availability.")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP error {e.response.status_code} from {url}: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        # Catch any other requests-related errors
        print(f"ERROR: An unexpected error occurred while fetching data from {url}: {e}")
        return None
    except ValueError: # JSONDecodeError inherits from ValueError
        print(f"ERROR: Failed to decode JSON from response from {url}.")
        return None

def get_apod_content():
    """
    Fetches and formats Astronomy Picture of the Day data.
    Handles both image and video APODs.
    Returns:
        str: Markdown formatted string for the APOD section.
    """
    print("Fetching APOD data...")
    params = {"api_key": NASA_API_KEY}
    data = fetch_api_data(APOD_API_URL, params=params)
    
    if not data:
        return """
### Astronomy Picture of the Day (APOD)

Could not retrieve today's Astronomy Picture of the Day. Please check back later!
"""

    title = data.get("title", "No Title Available")
    explanation = data.get("explanation", "No explanation available.")
    date = data.get("date", "Unknown Date")
    
    image_url = "https://via.placeholder.com/600x400.png?text=Image+Not+Available" # Default placeholder

    # Determine the correct URL for the image or a suitable placeholder for video
    if data.get("media_type") == "video":
        # For videos, NASA APOD sometimes provides a thumbnail_url.
        # If not, use a generic video placeholder and link to the actual video.
        image_url = data.get("thumbnail_url", "https://via.placeholder.com/600x400.png?text=APOD+Video")
        video_link = f"[Watch Today's APOD Video]({data.get('url', '#')})"
        explanation_formatted = f"{explanation}\n\n*Note: Today's APOD is a video. {video_link}*"
    else:
        # Prefer HD image if available, otherwise use the regular URL.
        image_url = data.get("hdurl", data.get("url", image_url))
        explanation_formatted = explanation
    
    # Construct the Markdown string for the APOD section
    content = f"""
### Astronomy Picture of the Day (APOD)

![{title}]({image_url})
**Title:** {title}
**Date:** {date}

{explanation_formatted}
"""
    return content

def get_people_in_space_content():
    """
    Fetches data on people currently in space and formats it for Markdown.
    Returns:
        str: Markdown formatted string for the People in Space section.
    """
    print("Fetching People in Space data...")
    data = fetch_api_data(PEOPLE_IN_SPACE_API_URL)

    if not data:
        return """
### 👨‍🚀 Humans Among the Stars

Could not retrieve data on people in space. Please check back later!
"""

    number = data.get("number", 0)
    people = data.get("people", [])

    people_list_md = ""
    if people:
        for person in people:
            people_list_md += f"* {person.get('name', 'Unknown Astronaut')} ({person.get('craft', 'Unknown Craft')})\n"
    else:
        people_list_md = "* No specific names available at this time.\n"

    content = f"""
### 👨‍🚀 Humans Among the Stars

There are currently **{number}** people in space!

**Onboard:**
{people_list_md}
"""
    return content

def get_iss_location_content():
    """
    Fetches the current ISS location data and formats it for Markdown.
    Returns:
        str: Markdown formatted string for the ISS Location section.
    """
    print("Fetching ISS Location data...")
    data = fetch_api_data(ISS_LOCATION_API_URL)

    if not data:
        return """
### 🛰️ Where is the ISS Right Now?

Could not retrieve ISS location data. Please check back later!
"""

    iss_position = data.get("iss_position", {})
    latitude = iss_position.get("latitude", "N/A")
    longitude = iss_position.get("longitude", "N/A")
    
    # Convert Unix timestamp (seconds since epoch) to human-readable UTC time.
    # It's important to specify timezone.utc for consistency.
    timestamp = data.get("timestamp")
    if timestamp:
        try:
            dt_object = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            iss_timestamp_utc = dt_object.strftime('%Y-%m-%d %H:%M:%S UTC')
        except (TypeError, ValueError):
            iss_timestamp_utc = "Invalid Timestamp"
    else:
        iss_timestamp_utc = "N/A"

    content = f"""
### 🛰️ Where is the ISS Right Now?

The International Space Station is currently located at:
* **Latitude:** `{latitude}`
* **Longitude:** `{longitude}`
*(As of {iss_timestamp_utc})*

*(Note: Coordinates update hourly. For a live map, you can visit [Where The ISS At?](http://wheretheiss.at/))*
"""
    return content

def generate_readme_content():
    """
    Assembles all the fetched content into the complete README Markdown string.
    Returns:
        str: The full Markdown content for the README.md file.
    """
    # Get the current time in UTC for the "Last updated" timestamp.
    current_update_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    # Retrieve Markdown content for each section
    apod_section_md = get_apod_content()
    people_section_md = get_people_in_space_content()
    iss_section_md = get_iss_location_content()

    # Get the repository name from GitHub Actions environment variable
    # This makes the "open-source" link dynamic and correct for your repo.
    # GITHUB_REPOSITORY is automatically set by GitHub Actions (e.g., 'your-username/your-username').
    repo_name = os.getenv('GITHUB_REPOSITORY', 'YOUR_USERNAME/YOUR_USERNAME') 

    # Assemble the full README content using an f-string for easy insertion
    readme_template = f"""
# ✨ Welcome to my GitHub profile! This README is dynamically updated with fascinating insights from the cosmos. ✨

{apod_section_md}

---

{people_section_md}

---

{iss_section_md}

---

*Last updated: {current_update_time}*
"""
    return readme_template.strip() # .strip() removes leading/trailing whitespace

def update_readme_file():
    """
    The main function to orchestrate data fetching, content generation,
    and writing the content to the README.md file.
    """
    print("Starting README update process...")
    new_readme_content = generate_readme_content()

    # Construct the correct path to README.md.
    # os.path.dirname(__file__) gets the directory of the current script (scripts/).
    # '..' moves up one level to the parent directory (your_username/ repository root).
    # 'README.md' is the target file.
    readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
    
    try:
        # Open the README.md file in write mode ('w').
        # 'encoding="utf-8"' ensures proper handling of various characters (e.g., emojis).
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_readme_content)
        print(f"Successfully updated README.md at: {readme_path}")
    except Exception as e:
        print(f"ERROR: Failed to write to README.md at {readme_path}: {e}")

# This ensures update_readme_file() runs only when the script is executed directly.
if __name__ == "__main__":
    update_readme_file()