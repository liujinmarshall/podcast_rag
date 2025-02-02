import google.generativeai as genai
import os
import csv
import json
from typing import List
import subprocess
from util import *

model = init_model()

def transcribe_audio_with_history(audio_file_path: str, initial_prompt: str, continuous_prompt: str) -> str:
    """
    Transcribes an audio file using Google Gemini API, handling potentially
    large outputs by maintaining conversation history.

    Args:
        audio_file_path: Path to the audio file.

    Returns:
        The full transcribed text.
    """
    try:
        audio_file = upload_to_gemini(audio_file_path, mime_type="audio/mpeg")
        # Start the conversation
        chat = model.start_chat(
            history=[{
                    "role": "user",
                    "parts": [audio_file],
                }
            ]
        )

        response = chat.send_message(initial_prompt, request_options={"timeout": 1000})

        full_transcription = response.text

        print("\nInitial transcription complete. Checking for potential truncation...")

        # Check if the response might be truncated (this is an approximation, actual API behavior might vary)
        # With 1.5 Pro, the context window is large, but it's good practice to handle potential truncation
        print(response.candidates[0].finish_reason)
        while str(response.candidates[0].finish_reason) != 'FinishReason.STOP':  # 'STOP' typically indicates a natural end
        #if True:
            print("Continuing transcription...")
            # Create a new turn in the conversation, asking to continue
            contents = [
                {
                    "parts": [
                        continuous_prompt
                    ]
                }
            ]
            response = chat.send_message(continuous_prompt, request_options={"timeout": 1000})
            full_transcription += response.text

        print("\nTranscription complete.")
        return full_transcription

    except FileNotFoundError:
        print(f"Error: Audio file not found at {audio_file_path}")
        return ""
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        return ""


def transcript_audiofile(audio_file, podcast_name, podcast_language,podcast_title, podcast_shownotes):
    if (len(audio_file) == 0):
        return
    download_dir = CONFIG["transcript_directory"] + "/" + podcast_name
    transcript_filename = download_dir + "/" + audio_file + ".transcript.txt"
    if (check_file_exists_and_size(transcript_filename, 100)):
        #print(f"{transcript_filename} exists... skip transcribing...")
        return
    prompts = read_prompts()
    #initial_prompt = f"这是播客《{podcast_name}》的一期节目，请生成音频记录，包括每个转录的说话者信息和时间轴（开始时间），按照事件发生的时间来组织转录。播客标题: {podcast_title}。播客shownotes: {podcast_shownotes}"
    #continuous_prompt = "请根据上面已经生成的内容继续生成转录文字稿。"
    initial_prompt = prompts[podcast_language]['initial_prompt'].format(podcast_name=podcast_name, podcast_title=podcast_title, podcast_shownotes=podcast_shownotes)
    continuous_prompt = prompts[podcast_language]['continuous_prompt']
    transcribed_text = transcribe_audio_with_history(CONFIG["audio_download_directory"] + "/" + podcast_name + "/" + audio_file, initial_prompt, continuous_prompt)

    if transcribed_text:
        print(f"--- Full Transcribed Text for {audio_file} ---")
        os.makedirs(download_dir, exist_ok=True)
        
        # You can save the transcribed text to a file if needed
        with open(transcript_filename, "w") as f:
            f.write(transcribed_text)
    
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
                print(f"Error loading previous data for {podcast['podcast_name']}: {e}")
        #print(previous_episodes)
    
        for episode in previous_episodes:
            transcript_episode(previous_episodes[episode], podcast['podcast_name'], podcast['language'])

def transcript_episode(episode, podcast_name, language):
    print(episode["title"])
    transcript_audiofile(episode["filename"], get_safe_podcast_name(podcast_name), language, episode["title"], episode["description"])

if __name__ == "__main__":
    process_podcast_data()
