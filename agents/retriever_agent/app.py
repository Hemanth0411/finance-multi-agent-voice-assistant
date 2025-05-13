from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import os
from dotenv import load_dotenv
<<<<<<< Updated upstream
=======
import time
import logging
from data_ingestion.data_utils import log_duration

# Add project root to sys.path
PROJECT_ROOT_RETRIEVER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT_RETRIEVER not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_RETRIEVER)
>>>>>>> Stashed changes

load_dotenv()
logger = logging.getLogger(__name__)

# --- Configuration ---
DIMENSION = 384 # Dimension for all-MiniLM-L6-v2
FAISS_INDEX_PATH = "./faiss_index.bin" # Optional: Path to save/load index
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2") # Added

# --- Data and Model Loading ---
# Dummy document store (Replace with actual data loading if needed)
document_store = {
    0: "Market sentiment is cautiously optimistic regarding tech stocks.",
    1: "Rising interest rates pose a potential headwind for growth sectors.",
    2: "TSMC reported strong earnings, beating analyst expectations significantly.",
    3: "Samsung Electronics provided mixed guidance, citing chip division challenges but strong mobile sales.",
    4: "Geopolitical tensions in the Asia-Pacific region remain a key risk factor for semiconductor supply chains."
}

# Global variables for model and index
model = None
index = None
faiss_ids = [] # To map FAISS results back to document_store keys

# Moved App definition up
app = FastAPI(
    title="Retriever Agent Service",
    description="Retrieves relevant document chunks based on semantic query.",
    version="0.1.0"
)

@app.on_event("startup")
async def load_model_and_index():
    global model, index, faiss_ids
    logger.info(f"Loading SentenceTransformer model: {EMBEDDING_MODEL_NAME}...")
    try:
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info("SentenceTransformer model loaded.")
    except Exception as e:
        logger.error(f"Error loading SentenceTransformer model: {e}", exc_info=True)
        raise RuntimeError("Failed to load SentenceTransformer model") from e

    # --- Build FAISS Index ---
    # Optional: Load index if it exists
    # if os.path.exists(FAISS_INDEX_PATH):
    #     try:
    #         index = faiss.read_index(FAISS_INDEX_PATH)
    #         # You would also need to load the corresponding faiss_ids mapping
    #         print(f"Loaded FAISS index from {FAISS_INDEX_PATH}")
    #     except Exception as e:
    #         print(f"Error loading FAISS index from {FAISS_INDEX_PATH}: {e}. Rebuilding...")
    #         index = None # Ensure index is rebuilt

    if not index:
        logger.info("Building FAISS index from document store...")
        try:
            doc_texts = list(document_store.values())
            faiss_ids = list(document_store.keys()) # Store original keys

            if not doc_texts:
                 logger.warning("Document store is empty. FAISS index will be empty.")
                 index = faiss.IndexFlatIP(DIMENSION) # Create empty index
                 return

            logger.info(f"Embedding {len(doc_texts)} documents...")
            embeddings = model.encode(doc_texts, convert_to_numpy=True)

            # Ensure embeddings are float32
            embeddings = np.float32(embeddings)

            # Normalize embeddings for Inner Product (Cosine Similarity)
            faiss.normalize_L2(embeddings)

            # Create FAISS index
            index = faiss.IndexFlatIP(DIMENSION) # Inner Product index
            # Add embeddings to the index
            index.add(embeddings)

            logger.info(f"FAISS index built successfully with {index.ntotal} vectors.")

            # Optional: Save index
            # try:
            #     faiss.write_index(index, FAISS_INDEX_PATH)
            #     # You would also save the faiss_ids mapping here
            #     print(f"Saved FAISS index to {FAISS_INDEX_PATH}")
            # except Exception as e:
            #     print(f"Error saving FAISS index: {e}")

        except Exception as e:
            logger.error(f"Error building FAISS index: {e}", exc_info=True)
            index = None # Ensure index is None if build fails

# app = FastAPI( # Removed from here
#     title="Retriever Agent Service",
#     description="Retrieves relevant document chunks based on semantic query.",
#     version="0.1.0"
# )

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class RetrievalResponse(BaseModel):
    results: list[dict] # List of {'id': int, 'text': str, 'score': float}

@app.post("/retrieve", response_model=RetrievalResponse, summary="Retrieve Documents", description="Finds the most relevant document chunks for a given query using semantic search.")
async def retrieve_documents(request: QueryRequest):
    """Endpoint to retrieve relevant document chunks.

    Args:
        request: QueryRequest containing the search query and desired number of results (top_k).

    Returns:
        RetrievalResponse containing the top_k relevant documents and their scores.

    Raises:
        HTTPException: 500 if retrieval fails or index/model not loaded.
    """
    if not model or not index:
        raise HTTPException(status_code=500, detail="Model or FAISS index not loaded.")
    if index.ntotal == 0:
         logger.warning("Attempting to search an empty FAISS index.")
         return RetrievalResponse(results=[])

    try:
        query_embedding = model.encode([request.query])[0]
        # Normalize query embedding
        query_embedding_normalized = np.float32(query_embedding)
        faiss.normalize_L2(query_embedding_normalized.reshape(1, -1))

        # Ensure k is not larger than the number of documents in the index
        k = min(request.top_k, index.ntotal)
        if k <= 0:
             return RetrievalResponse(results=[])

        # Perform FAISS search
        # D = distances (inner product scores), I = indices
        logger.info(f"Searching FAISS index for top {k} results...")
        distances, indices = index.search(query_embedding_normalized.reshape(1, -1), k)

        results = []
        if indices.size > 0:
            for i in range(indices.shape[1]): # Iterate through the k results
                 faiss_index = indices[0, i]
                 score = distances[0, i]
                 # Map internal FAISS index back to original document key
                 original_doc_id = faiss_ids[faiss_index]
                 results.append({
                     "id": int(original_doc_id),
                     "text": document_store.get(original_doc_id, "Document not found"),
                     "score": float(score) # Inner Product score (higher is better)
                 })

<<<<<<< Updated upstream
        print(f"Retrieved {len(results)} results.")
        return RetrievalResponse(results=results)
    except Exception as e:
        print(f"Error during retrieval: {e}")
        # Log the exception traceback for debugging
        import traceback
        traceback.print_exc()
=======
        logger.info(f"Retrieved {len(results)} results from FAISS index.")
        log_duration("Retriever_Agent_Total_Request", retriever_total_req_start_time)
        return RetrievalResponse(results=results)
    except Exception as e:
        logger.error(f"Error during retrieval: {e}", exc_info=True)
        log_duration("Retriever_Agent_Total_Request_Error", retriever_total_req_start_time)
>>>>>>> Stashed changes
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {e}")

# The following __main__ block is for local testing and should be removed for deployment.
# # Removed if __name__ == "__main__" block for deployment
# # if __name__ == "__main__":
# #     import uvicorn
# #     # Run using:
# #     # cd finance-assistant
# #     # uvicorn agents.retriever_agent.app:app --reload --port 8002
# #     # logger.info("Running Retriever Agent Service. Access docs at http://localhost:8002/docs")
# #     # Ensure model is loaded before starting server
# #     # if 'model' not in globals() or model is None or index is None: # Check index as well
# #     #     logger.error("SentenceTransformer model or FAISS index not loaded properly. Exiting.")

# This active __main__ block is now being removed:
# if __name__ == "__main__":
#     import uvicorn
#     # Run using:
#     # cd finance-assistant
#     # uvicorn agents.retriever_agent.app:app --reload --port 8002
#     print("Running Retriever Agent Service. Access docs at http://localhost:8002/docs")
#     # Ensure model is loaded before starting server
#     if 'model' not in globals():
#         print("SentenceTransformer model not loaded. Exiting.")
#     else:
#         uvicorn.run(app, host="0.0.0.0", port=8002) 