import gradio as gr
import chromadb
from util import *

TOP_K_RETRIEVAL = 30

# --- Retrieval and Generation Functions ---
def retrieve_relevant_chunks(query, top_k=TOP_K_RETRIEVAL):
    print(query)
    #query_embedding = generate_embeddings_batch([query])
    #print(query_embedding)
    results = collection.query(
        #query_embeddings=query_embedding,
        query_texts = query,
        n_results=top_k
    )
    #print(results)
    return results

def generate_response(query, context_chunks):
    context = "\n\n".join(context_chunks)
    prompt = f"""根据提供的上下文（5个*之间）回答下面的问题（5个&之间），并提供相应的播客信息。

    上下文:
    *****{context}*****

    问题: &&&&&{query}&&&&&
    """
    response = model.generate_content(prompt)
    return response.text

# --- Chatbot Interface ---
def chatbot(query):
    retrieved_chunks = retrieve_relevant_chunks(query)
    if retrieved_chunks and retrieved_chunks['documents']:
        context_chunks = retrieved_chunks['documents'] # Using top K now
        #print(context_chunks)
        response = generate_response(query, context_chunks[0])
        return response
    else:
        return "I couldn't find relevant information in the podcast transcripts for that question."

iface = gr.Interface(
    fn=chatbot,
    inputs=gr.Textbox(placeholder="Ask me anything about the podcasts!"),
    outputs=gr.Textbox(),
    title="Podcast Chatbot",
    description="Ask questions about the content of the transcribed podcasts."
)

collection_name = CONFIG["vector_collection"]
client = chromadb.PersistentClient(path=CONFIG["index_directory"])
collection = client.get_or_create_collection(name=collection_name, embedding_function=openai_ef)
print(f"Collection '{collection_name}' loaded/created.")

model = init_model()

iface.launch()