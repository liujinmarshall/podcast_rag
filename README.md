# podcast_rag
Use RAG (Retrieval Augmentation Generation) to understand podcast

Tested Python Version: 3.9 (should also work on later versions and versions that are not too old)

## Prerequisites
1. Python envionment and know how to run
2. Google Gemini API Key and OpenAI API Key

## Steps
1. Clone this github repo
2. Copy podcasts.example.csv to podcasts.csv and add RSS URL entries
3. Install python dependencies from requirements.txt
4. Export Google Gemini API Key as GEMINI_API_KEY and OpenAI API Key as OPENAI_API_KEY
5. Run following script to achieve the functionality below (using python xxx.py)
    1. download.py: Download podcast audio media files to local with incremental mode. One directory for each podcast 
    2. transcribe.py: Transcribe the audio media files into transcription. One directory for each podcast
    3. index.py: Chunk and index the transcription into vectordb(ChromaDB)
    4. query.py: Start a chatbot to query the question
	    1. Run the program
	    2. Open the link in browser and start to ask questions <img src="https://github.com/liujinmarshall/rag_podcast/blob/main/docs/img/chatbot.png?raw=true" />
    5. summarize.py: Summarize the transcription into a concise summary. One directory for each podcast
    6. delete_files.py: Remove audio media files (older than 24 hours) in case the file upload exceeds quota. Anyway the files uploaded for more than 48 hours will be purged automatically

## Language Support
* Chinese
* English (to be added)

## History
* 1/26/2025: 0.01 (Initial Release)