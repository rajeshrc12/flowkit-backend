from langchain_community.document_loaders import PyPDFLoader
import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_voyageai import VoyageAIEmbeddings

load_dotenv()

# Initialize embeddings
embedding = VoyageAIEmbeddings(
    model="voyage-3.5-lite",
    voyage_api_key=os.getenv("VOYAGE_API_KEY")
)

def store_pdf_in_pinecone(pdf_path):
    """
    Load PDF, split into chunks, and store in Pinecone
    
    Args:
        pdf_path (str): Path to the PDF file
    """
    # Load PDF
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    
    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(docs)
    
    # Store in Pinecone
    PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embedding,
        index_name=os.getenv("PINECONE_INDEX_NAME")
    )
    
    print(f"✅ Stored {len(chunks)} chunks from {pdf_path} in Pinecone")

def retrieve_from_pinecone(query):
    """
    Search Pinecone for relevant documents based on query
    
    Args:
        query (str): Search query
        
    Returns:
        list: Relevant documents
    """
    # Connect to existing Pinecone index
    vector_store = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        embedding=embedding
    )
    
    # Search for relevant documents
    results = vector_store.similarity_search(query, k=4)
    
    print(f"🔍 Found {len(results)} relevant documents for: '{query}'")
    return results

# Usage example:
if __name__ == "__main__":
    # Store PDF
    store_pdf_in_pinecone("p3.pdf")
    
    # Retrieve relevant data
    while True:
        query = input(">")
        try:
            results = retrieve_from_pinecone(query)
        except Exception as e:
            print(str(e))
        # Print results
        for i, doc in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(doc.page_content)