import os
import csv
import subprocess
import google.generativeai as genai
import chromadb.utils.embedding_functions as embedding_functions

data_dir = "data"

# Configuration
CONFIG = {
    "gemini_key": "",
    "podcast_list_file": f"{data_dir}/podcasts.csv",
    "output_directory": f"{data_dir}/podcast_data",
    "audio_download_directory": f"{data_dir}/podcast_audio",
    "transcript_directory": f"{data_dir}/podcast_transcript",
    "summary_directory": f"{data_dir}/podcast_summary",
    "index_directory": f"{data_dir}/chroma_db",
    "vector_collection" : "podcast_embeddings",
    "embedding_batch_size" : 100
}

def check_file_exists_and_size(filename, min_size_bytes):
  """
  Checks if a file exists and its size is larger than a specified value.

  Args:
    filename (str): The path to the file.
    min_size_bytes (int): The minimum file size in bytes that the file must exceed.

  Returns:
    bool: True if the file exists and its size is greater than min_size_bytes, False otherwise.
  """
  if not isinstance(filename, str):
    raise TypeError("filename must be a string")
  if not isinstance(min_size_bytes, int):
    raise TypeError("min_size_bytes must be an integer")
  if min_size_bytes < 0:
    raise ValueError("min_size_bytes cannot be negative")

  if os.path.exists(filename) and os.path.isfile(filename):
    try:
      file_size = os.path.getsize(filename)
      return file_size > min_size_bytes
    except OSError:
      # Handle cases where the file exists but we can't get its size
      # (e.g., permissions issues)
      return False
  else:
    return False

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file


def get_gemini_key():
    # Run a command and get its output
    return os.environ.get("GEMINI_API_KEY")

def init_model():
    api_key = get_gemini_key()
    
    # Configure the API key
    genai.configure(api_key=api_key)

    # Create the model
    generation_config = {
      "temperature": 1,
      "top_p": 0.95,
      "top_k": 40,
      "max_output_tokens": 8192,
      "response_mime_type": "text/plain",
    }
    # Select the Gemini Flash 1.5 model
    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)
    return model

# Function to read podcast list from CSV
def read_podcast_list(filename):
    podcasts = []
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                podcasts.append(row)
    except FileNotFoundError:
        print(f"Error: Podcast list file not found: {filename}")
    print(podcasts)
    return podcasts

def get_safe_podcast_name(podcast_name):
    return "".join(c if c.isalnum() else '_' for c in podcast_name)


openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)