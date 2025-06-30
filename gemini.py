from langchain.embeddings.base import Embeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
from typing import List
import os
import google.generativeai as genai

# Load env variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Gemini embedding function


def get_gemini_embedding(text: str) -> List[float]:
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return result["embedding"]


# Custom wrapper for LangChain-compatible embedding class


class GeminiEmbeddings(Embeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [get_gemini_embedding(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return get_gemini_embedding(text)


# Initialize Gemini embedding wrapper
embedding = GeminiEmbeddings()


def store_pdf_in_pinecone(pdf_path: str):
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    # Store in Pinecone
    PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embedding,
        index_name=os.getenv("PINECONE_INDEX_NAME")
    )
    print(f"✅ Stored {len(chunks)} chunks from {pdf_path} in Pinecone")


def retrieve_from_pinecone(query: str):
    vector_store = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        embedding=embedding
    )
    results = vector_store.similarity_search(query, k=4)
    print(f"🔍 Found {len(results)} relevant documents for: '{query}'")
    return results


# Example usage
if __name__ == "__main__":
    store_pdf_in_pinecone("p1.pdf")

    while True:
        query = input("\nYour query: ")
        try:
            results = retrieve_from_pinecone(query)
            for i, doc in enumerate(results, 1):
                print(f"\nResult {i}:\n{doc.page_content}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
