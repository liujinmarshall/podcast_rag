import csv
import requests
import xml.etree.ElementTree as ET
import json
import os
from bs4 import BeautifulSoup
import time
import argparse
from datetime import datetime
from urllib.parse import urlparse
from util import *

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}

# Function to fetch RSS feed content
def fetch_rss_feed(rss_url):
    print(rss_url)
    try:        
        response = requests.get(rss_url, timeout=10, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching RSS feed from {rss_url}: {e}")
        return None

# Function to strip HTML tags from a string
def strip_html_tags(html_string):
    soup = BeautifulSoup(html_string, "html.parser")
    return soup.get_text(separator=" ", strip=True)

# Function to parse RSS XML and convert to JSON
def parse_rss_and_convert_to_json(rss_content):
    podcast_data = {"episodes": []}
    try:
        root = ET.fromstring(rss_content)
        channel = root.find("channel")
        if channel is not None:
            podcast_data["title"] = channel.findtext("title")
            podcast_data["description"] = strip_html_tags(channel.findtext("description", ""))
            podcast_data["link"] = channel.findtext("link")

            for item in channel.findall("item"):
                episode = {
                    "title": item.findtext("title"),
                    "link": item.findtext("link"),
                    "description": strip_html_tags(item.findtext("description", "")),
                    "pubDate": item.findtext("pubDate"),
                    "enclosure_url": None,
                    "enclosure_type": None,
                    "guid": item.findtext("guid") # Assuming guid is available
                }
                enclosure = item.find("enclosure")
                if enclosure is not None:
                    episode["enclosure_url"] = enclosure.get("url")
                    episode["enclosure_type"] = enclosure.get("type")
                podcast_data["episodes"].append(episode)
    except ET.ParseError as e:
        print(f"Error parsing RSS XML: {e}")
    return podcast_data

# Helper function to parse pubDate string to datetime object
def parse_pub_date(date_string):
    # Attempt to parse with different common formats
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M %Z",
        "%a, %d %b %Y %H:%M %z",
        "%d %b %Y %H:%M:%S %Z",
        "%d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            pass
    return None

def get_file_extension(url):
    """Extracts the file extension from a URL.

    Args:
        url: The URL string.

    Returns:
        The file extension (lowercase) or None if no extension is found.
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    if not path:
        return None

    # Use os.path.splitext to split the filename and extension
    filename = os.path.basename(path)
    name, ext = os.path.splitext(filename)

    if ext:
        return ext[1:].lower()  # Remove the leading dot and lowercase
    else:
        return None

# Hook function to process an episode (stub)
def process_episode(episode_data, podcast_name):
    enclosure_url = episode_data.get("enclosure_url")
    if enclosure_url and (enclosure_url.endswith(".mp3") or enclosure_url.endswith(".m4a")):
        print("Processing episode: " + episode_data["enclosure_url"])
        (episode_data["filename"], episode_data["filesize"]) = download_audio(
            episode_data["enclosure_url"], podcast_name, episode_data["title"], episode_data.get("pubDate"))
    else:
        print(f"No MP3/M4A enclosure found for episode: {episode_data.get('title')}")

# Function to download audio file
def download_audio(audio_url, podcast_name, episode_title, pub_date_str):
    safe_podcast_name = get_safe_podcast_name(podcast_name)
    safe_episode_title = "".join(c if c.isalnum() or c in [' ', '.', '-'] else '_' for c in episode_title)
    download_dir = CONFIG["audio_download_directory"] + "/" + safe_podcast_name
    os.makedirs(download_dir, exist_ok=True)

    pub_date = parse_pub_date(pub_date_str)
    date_str = ""
    file_ext = get_file_extension(audio_url)
    if pub_date:
        date_str = pub_date.strftime("%Y-%m-%d")
        short_filename = f"{date_str}_{safe_podcast_name}_{safe_episode_title}.{file_ext}"
    else:
        short_filename = f"nodate_{safe_podcast_name}_{safe_episode_title}.{file_ext}"
        print(f"Warning: Could not parse pubDate for '{episode_title}'. Saving without date.")

    filename = os.path.join(download_dir, short_filename)
    # Check if the file exists
    if os.path.exists(filename):
        try:
            # Get the size of the existing file
            existing_file_size = os.path.getsize(filename)

            # Get the size of the file at the URL using HEAD request
            head_response = requests.head(audio_url, allow_redirects=True, headers=headers)
            head_response.raise_for_status()  # Raise an exception for bad status codes
            remote_file_size = int(head_response.headers.get('Content-Length', 0))

            if existing_file_size == remote_file_size:
                print(f"This {filename} already exists and skip downloading.")
                return (short_filename, remote_file_size)
            else:
                print(f"File {filename} exists but size mismatch. Old size: {existing_file_size}, New size: {remote_file_size}. Removing existing file.")
                os.remove(filename)
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not get remote file size for {audio_url}: {e}. Proceeding with download.")
        except Exception as e:
            print(f"Warning: Error checking existing file {filename}: {e}. Proceeding with download.")

    # Download the file if it doesn't exist or the size doesn't match
    try:
        print(f"Downloading audio for '{episode_title}' from '{podcast_name}' (published {date_str if date_str else 'unknown date'})...")
        response = requests.get(audio_url, stream=True, headers=headers)
        response.raise_for_status()
        written_size = 0
        
        with open(filename, 'wb') as outfile:
            for chunk in response.iter_content(chunk_size=8192):
                outfile.write(chunk)
                written_size += len(chunk)
        print(f"Audio downloaded to: {filename}")
        # Sleep 10 seconds after successful download otherwise might be banned
        time.sleep(10)
        return (short_filename, written_size)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading audio from {audio_url}: {e}")
        return ("", 0)
    except Exception as e:
        print(f"An error occurred during audio download: {e}")
        return ("", 0)

# Function to save podcast data to a JSON file
def save_podcast_data(podcast_name, podcast_data):
    os.makedirs(CONFIG["output_directory"], exist_ok=True)
    safe_podcast_name = "".join(c if c.isalnum() else '_' for c in podcast_name)
    filename = os.path.join(CONFIG["output_directory"], f"{safe_podcast_name}.json")
    try:
        with open(filename, 'w', encoding='utf-8') as outfile:
            json.dump(podcast_data, outfile, indent=4, ensure_ascii=False)  # Added ensure_ascii=False
        print(f"Podcast data saved to: {filename}")
    except Exception as e:
        print(f"Error saving podcast data to {filename}: {e}")

# Function for full mode processing
def process_podcast_full(podcast):
    print(f"Processing podcast (Full Mode): {podcast['podcast_name']}")
    rss_content = fetch_rss_feed(podcast['rss_url'])
    if rss_content:
        podcast_data = parse_rss_and_convert_to_json(rss_content)
        # Sort episodes by pubDate ascending
        podcast_data["episodes"].sort(key=lambda x: parse_pub_date(x.get("pubDate")) if x.get("pubDate") else datetime.min)
        save_podcast_data(podcast['podcast_name'], podcast_data)
        for episode in podcast_data.get("episodes", []):
            process_episode(episode, podcast['podcast_name'])

# Function for incremental mode processing
def process_podcast_incremental(podcast):
    print(f"Processing podcast (Incremental Mode): {podcast['podcast_name']}")
    safe_podcast_name = "".join(c if c.isalnum() else '_' for c in podcast['podcast_name'])
    previous_data_file = os.path.join(CONFIG["output_directory"], f"{safe_podcast_name}.json")
    previous_episodes = {}
    if os.path.exists(previous_data_file):
        try:
            with open(previous_data_file, 'r', encoding='utf-8') as infile:
                previous_data = json.load(infile)
                previous_episodes = {ep["guid"]: ep for ep in previous_data.get("episodes", []) if ep.get("guid")}
        except Exception as e:
            print(f"Error loading previous data for {podcast['podcast_name']}: {e}")

    rss_content = fetch_rss_feed(podcast['rss_url'])
    print(f"RSS Length:{len(rss_content)}")
    if rss_content:
        current_podcast_data = parse_rss_and_convert_to_json(rss_content)
        # Sort episodes by pubDate ascending
        current_podcast_data["episodes"].sort(key=lambda x: parse_pub_date(x.get("pubDate")) if x.get("pubDate") else datetime.min)
        print("current_podcast_data: " + str(len(current_podcast_data.get("episodes", []))))
        #print(current_podcast_data)
        print("previous_episodes: " + str(len(previous_episodes)))
        new_episodes = []
        for episode in current_podcast_data.get("episodes", []):
            if episode.get("guid") and episode["guid"] not in previous_episodes:
                new_episodes.append(episode)
                process_episode(episode, podcast['podcast_name'])

        if new_episodes:
            print(f"Found {len(new_episodes)} new episodes for {podcast['podcast_name']}")
            # Update and save the podcast data with new episodes
            if os.path.exists(previous_data_file):
                try:
                    with open(previous_data_file, 'r+', encoding='utf-8') as infile:
                        previous_data = json.load(infile)
                        existing_guids = {ep.get("guid") for ep in previous_data.get("episodes", []) if ep.get("guid")}
                        for new_ep in new_episodes:
                            if new_ep.get("guid") and new_ep["guid"] not in existing_guids:
                                previous_data["episodes"].append(new_ep)
                        # Sort the combined episodes before saving
                        previous_data["episodes"].sort(key=lambda x: parse_pub_date(x.get("pubDate")) if x.get("pubDate") else datetime.min)
                        infile.seek(0)
                        json.dump(previous_data, infile, indent=4, ensure_ascii=False)
                        infile.truncate()
                except Exception as e:
                    print(f"Error updating previous data for {podcast['podcast_name']}: {e}")
            else:
                save_podcast_data(podcast['podcast_name'], current_podcast_data) # Save all if no previous data
        else:
            print(f"No new episodes found for {podcast['podcast_name']}")



# Main function
def download_podcast():
    parser = argparse.ArgumentParser(description="Download podcast audio files")
    parser.add_argument('--mode',
                    type=str,  # Expect a string value
                    help='The mode to run the script in (e.g., full, incremental)')
    args = parser.parse_args()
    # Choose mode: 'full' or 'incremental'
    mode = 'incremental'  # Change to 'full' for full mode
    if args.mode:
        mode = args.mode
    
    podcasts = read_podcast_list(CONFIG["podcast_list_file"])
    if not podcasts:
        return
        
    os.makedirs(CONFIG["output_directory"], exist_ok = True)

    if mode == 'full':
        for podcast in podcasts:
            process_podcast_full(podcast)
    elif mode == 'incremental':
        for podcast in podcasts:
            process_podcast_incremental(podcast)
    else:
        print("Invalid mode selected.")

if __name__ == "__main__":
    download_podcast()