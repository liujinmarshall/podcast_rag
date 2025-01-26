# podcast_rag
Use RAG (Retrieval Augmentation Generation) to understand podcast

Tested Python Version: 3.9 (should also work on later versions and versions that are not too old)

## Prerequisites
1. Python envionment and know how to run
2. Google Gemini API Key and OpenAI API Key

## Steps
1. Clone this github repo
2. Make a directory "data"
3. Copy podcasts.example.csv to data/podcasts.csv and add RSS URL entries
4. Install python dependencies from requirements.txt (pip install -r requirments.txt)
5. Export Google Gemini API Key as GEMINI_API_KEY and OpenAI API Key as OPENAI_API_KEY
6. Run following script to achieve the functionality below (using python xxx.py)
    1. download.py: Download podcast audio media files to local with incremental mode. One directory for each podcast 
    2. transcribe.py: Transcribe the audio media files into transcription. One directory for each podcast
    3. index.py: Chunk and index the transcription into vectordb(ChromaDB)
    4. query.py: Start a chatbot to query the question
	    1. Run the program
	    2. Open the link in browser and start to ask questions <img src="https://raw.githubusercontent.com/liujinmarshall/podcast_rag/refs/heads/main/docs/img/chatbot.png" />
    5. summarize.py: Summarize the transcription into a concise summary. One directory for each podcast
    6. delete_files.py: Remove audio media files (older than 24 hours) in case the file upload exceeds quota. Anyway the files uploaded for more than 48 hours will be purged automatically

## Language Support
* Chinese
* English (to be added)

## Note
Please adhere to user agreement of podcast provider. This repo is for personal research purpose only.

## History
* 1/26/2025: 0.01 (Initial Release)
