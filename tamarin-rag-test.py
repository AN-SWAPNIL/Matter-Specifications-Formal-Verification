from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from typing import Optional, List, Dict, Any
import os

# Embedding model — same as you used
EMBED_MODEL = "gemini-embedding-001"
PERSIST_DIR = "tamarin_vectordb"
COLLECTION_NAME = "tamarin_manual"


if not os.environ.get("GOOGLE_API_KEY"): 
    os.environ["GOOGLE_API_KEY"] = "AIzaSyB4NYH0ShxD8OwCkRFGP8rIk-abzJ4TgIs"

def load_vector_store() -> Chroma:
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)
    vectorstore = Chroma(
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings
    )
    return vectorstore

def query_vectordb(
    query: str,
    k: int = 5,
    section: Optional[str] = None
) -> List[Document]:
    """
    Query the vector DB for the top-k most similar chunks to `query`.
    If `section` is provided, filter results to only that section (metadata).
    """
    vectorstore = load_vector_store()
    filter: Dict[str, Any] = None
    if section:
        filter = {"section": section}
    docs = vectorstore.similarity_search(query, k=k, filter=filter)
    return docs

if __name__ == "__main__":
    # Examples
    print("=== Query without section filter ===")
    for doc in query_vectordb("How to install Tamarin on Windows", k=10):
        print(doc.metadata, doc.page_content)
        print("---------------------------------------------------------------------------------------")

    # print("\n=== Query with section filter (e.g. 'Installation on Windows 10') ===")
    # for doc in query_vectordb("install Windows", k=5, section="Installation on Windows 10"):
    #     print(doc.metadata, doc.page_content)
