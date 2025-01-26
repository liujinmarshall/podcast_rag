import os
import google.generativeai as genai
from util import *
import tiktoken
import chromadb

model = init_model()

CHUNK_SIZE_TOKENS = 2000  # Chunk size in tokens
CHUNK_OVERLAP_TOKENS = 200  # Overlap in tokens
GPT4_ENCODING = "cl100k_base"
tokenizer = tiktoken.get_encoding(GPT4_ENCODING)

def load_podcast_transcripts(directory):
    """Loads podcast transcripts from text files in a directory."""
    transcripts = {}
    for filename in os.listdir(directory):
        if filename.endswith(".transcript.txt"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                transcripts[filename[:-4]] = f.read()  # Remove .txt extension
    return transcripts

def chunk_text(text, chunk_size=500, chunk_overlap=50):
    """Splits text into smaller chunks with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks

def chunk_text_by_tokens(text, chunk_size=CHUNK_SIZE_TOKENS, chunk_overlap=CHUNK_OVERLAP_TOKENS):
    """Splits text into smaller chunks based on token count using tiktoken with overlap."""
    tokens = tokenizer.encode(text)
    #print(len(tokens))
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        start = end - chunk_overlap
        if start < 0 or start + chunk_overlap == end:
            start = end  # Avoid negative start
    return chunks

COLLECTION_NAME = "podcast_embeddings"
EMBEDDING_BATCH_SIZE = CONFIG["embedding_batch_size"]


def index_transcript():
    # --- ChromaDB Setup ---
    client = chromadb.PersistentClient(path=CONFIG["index_directory"])
    try:
        collection_name = CONFIG["vector_collection"]
        collection = client.get_or_create_collection(name=collection_name, embedding_function=openai_ef)
        print(f"Collection '{collection_name}' loaded/created.")
    except ValueError:
        collection = client.create_collection(name=collection_name, embedding_function=openai_ef)
        print(f"Collection '{collection_name}' created.")
    
    podcasts = read_podcast_list(CONFIG["podcast_list_file"])
    if not podcasts:
        return

    for podcast in podcasts:
        print(f"Indexing podcast (Incremental Mode): {podcast['podcast_name']}")
        safe_podcast_name = get_safe_podcast_name(podcast['podcast_name'])
        podcast_directory = CONFIG["transcript_directory"] + "/" + safe_podcast_name
        raw_transcripts = load_podcast_transcripts(podcast_directory)

        all_documents = []
        all_metadatas = []
        all_ids = []

        for podcast_name, transcript in raw_transcripts.items():
            if (len(collection.get(ids=[f"{podcast_name}_chunk_0"])["ids"]) > 0):
                print(f"Skipping {podcast_name}")
                continue
            chunks = chunk_text_by_tokens(transcript)
            for i, chunk in enumerate(chunks):
                all_documents.append(chunk)
                all_metadatas.append({"source": podcast_name, "chunk": i})
                all_ids.append(f"{podcast_name}_chunk_{i}")
    
            # Generate and add embeddings in batches
            for i in range(0, len(all_documents), EMBEDDING_BATCH_SIZE):
                batch_documents = all_documents[i : i + EMBEDDING_BATCH_SIZE]
                batch_metadatas = all_metadatas[i : i + EMBEDDING_BATCH_SIZE]
                batch_ids = all_ids[i : i + EMBEDDING_BATCH_SIZE]
        
                #embeddings = generate_embeddings_batch(batch_documents)
                #print(len(embeddings))
                #print(len(embeddings[18]))
        
                #if embeddings:
                collection.add(
                    #embeddings=embeddings,
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                print(f"Indexed embeddings for documents {i} to {i + len(batch_documents) - 1}")
                # else:
                #     print(f"Error generating embeddings for documents {i} to {i + len(batch_documents) - 1}")

index_transcript()