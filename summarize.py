import google.generativeai as genai
import os
import csv
import json
from typing import List
import subprocess
from util import *
import time
from google.api_core.exceptions import ResourceExhausted

model = init_model()

def process_podcast_data():
    podcasts = read_podcast_list(CONFIG["podcast_list_file"])
    if not podcasts:
        return

    for podcast in podcasts:
        print(f"Processing podcast (Incremental Mode): {podcast['podcast_name']}")
        safe_podcast_name = get_safe_podcast_name(podcast['podcast_name'])
        previous_data_file = os.path.join(CONFIG["output_directory"], f"{safe_podcast_name}.json")
        previous_episodes = {}
        if os.path.exists(previous_data_file):
            try:
                with open(previous_data_file, 'r', encoding='utf-8') as infile:
                    previous_data = json.load(infile)
                    previous_episodes = {ep["guid"]: ep for ep in previous_data.get("episodes", []) if ep.get("guid")}
            except Exception as e:
                print(f"Error loading previous data for {safe_podcast_name}: {e}")
        #print(previous_episodes)
    
        for episode in previous_episodes:
            summarize_episode(previous_episodes[episode], safe_podcast_name, podcast['language'])

def summarize_episode(episode, podcast_name, language):
    if (len(episode["filename"]) == 0):
        return
    summarize_transcript(episode["filename"], podcast_name, language, episode["title"], episode["description"])

def summarize_transcript(audio_file, podcast_name, podcast_language, podcast_title, podcast_shownotes, max_retries=3):
    transcript_filename = CONFIG["transcript_directory"] + "/" + podcast_name + "/" + audio_file + ".transcript.txt"
    summary_filename = CONFIG["summary_directory"] + "/" + podcast_name + "/" + audio_file + ".summary.txt"

    transcript_detail = ""
        
    with open(transcript_filename, "r") as f:
        transcript_detail = f.read()

    if (len(transcript_detail) == 0):
        print(f"Empty transcript file {transcript_filename}")
        return
    
    if (check_file_exists_and_size(summary_filename, 100)):
        print(f"{summary_filename} exists... skip transcribing...")
        return
    
    initial_prompt = f"这是播客《{podcast_name}》的一期节目转录稿，在三个单引号之间。请根据提供的播客标题，shownotes和文字转录稿，生成这期播客的摘要。播客标题:{podcast_title}。播客shownotes:{podcast_shownotes}。'''{transcript_detail}'''"

    print(f"Summarize episode {audio_file}")

    retries = 0
    done = False
    while retries < max_retries and not done:
        try:
            response = model.generate_content(initial_prompt)
            time.sleep(1) # Otherwise will hit limit too soon
            if(response):
                done = True
        except ResourceExhausted as e:
            print(f"Quota limit reached (Attempt {retries + 1}). Error: {e}")
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                print("Sleeping for 1 minute before retrying...")
                time.sleep(60)
                retries += 1
            else:
                # It's a ResourceExhausted error but not likely a quota issue
                print("A ResourceExhausted error occurred that might not be quota-related. Aborting.")
                return None

    if (retries == max_retries):
        raise ResourceExhausted(f"No quota after {max_retries} retries")
        
    #print(response.text)
    with open(summary_filename, "w") as f:
        f.write(response.text)

process_podcast_data()