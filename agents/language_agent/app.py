from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
# from langchain_openai import ChatOpenAI # Example if using OpenAI
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
# --- LLM Imports ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# --- Import centralized prompt ---
from orchestrator.prompts import LANGUAGE_AGENT_PROMPT
# --- End LLM Imports ---

load_dotenv()

# Example: Load API key from environment variable (replace with your method)
# os.environ["OPENAI_API_KEY"] = "your-api-key"

# --- LLM Configuration ---
# Load API key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY environment variable not set. LLM calls will fail.")
    # Raise an error or handle appropriately if the key is critical for startup
    # raise ValueError("GOOGLE_API_KEY not set.")

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash-latest")

# Global variable for the LLM chain
chain = None

# Moved App definition up
app = FastAPI(
    title="Language Agent Service",
    description="Synthesizes narrative responses using LLM based on context and analysis.",
    version="0.1.0"
)

@app.on_event("startup")
async def load_llm_chain():
    global chain
    if not GOOGLE_API_KEY:
         print("LLM Chain cannot be loaded because GOOGLE_API_KEY is not set.")
         return
    
    print("Loading LLM chain...")
    try:
        # Initialize the LLM
        llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL_NAME, google_api_key=GOOGLE_API_KEY)

        # Define the prompt template - NOW IMPORTED
        # prompt_template = ChatPromptTemplate.from_messages([
        #     ("system", "You are a helpful financial assistant. Synthesize the provided data into a concise morning market brief answering the user's query. Focus on the key information requested."),
        #     ("user", "User Query: {query}\n\nPotentially Relevant Information (from documents):\n{context}\n\nQuantitative Analysis Results:\n{analysis}\n\nRecent Market Data Highlights:\n{market_highlights}\n\nGenerate a concise brief answering the query based *only* on the provided information. Start the brief directly without preamble.")
        # ])
        prompt_template = LANGUAGE_AGENT_PROMPT # Use the imported prompt

        # Define the output parser
        output_parser = StrOutputParser()

        # Create the LCEL chain
        chain = prompt_template | llm | output_parser
        print("LLM chain loaded successfully.")

    except Exception as e:
        print(f"Error loading LLM chain: {e}")
        import traceback
        traceback.print_exc()
        chain = None # Ensure chain is None if loading fails

class SynthesisRequest(BaseModel):
    query: str
    retrieved_context: List[Dict[str, Any]] # List of {'id': int, 'text': str, 'score': float}
    analysis_results: Dict[str, Any]
    market_data: Dict[str, Any]

class SynthesisResponse(BaseModel):
    narrative: str

# Placeholder for LangChain LLM setup
# llm = ChatOpenAI(model="gpt-3.5-turbo") # Or gpt-4, or other models/providers
# prompt_template = ChatPromptTemplate.from_messages([
#     ("system", "You are a helpful financial assistant. Synthesize the provided data into a concise morning market brief answering the user's query."),
#     ("user", "Query: {query}\n\nRetrieved Context:\n{context}\n\nAnalysis Results:\n{analysis}\n\nMarket Data Highlights:\n{market_highlights}\n\nBrief:")
# ])
# output_parser = StrOutputParser()
# chain = prompt_template | llm | output_parser

def format_context(context: List[Dict[str, Any]]) -> str:
    """Formats retrieved context for the LLM prompt."""
    if not context:
        return "No relevant documents found."
    return "\n".join([f"- {item['text']} (Score: {item['score']:.2f})" for item in context])

def format_analysis(analysis: Dict[str, Any]) -> str:
    """Formats analysis results for the LLM prompt."""
    items = []
    exposure = analysis.get('risk_metrics', {}).get('asia_tech_exposure_percent')
    if exposure is not None:
        items.append(f"- Asia Tech Exposure: {exposure}%")
    # Add formatting for other analysis metrics here
    if not items:
        return "No specific analysis results available."
    return "\n".join(items)

def format_market_data(market_data: Dict[str, Any]) -> str:
    """Formats key market data points for the LLM prompt."""
    highlights = []
    for symbol, data in market_data.items():
        if isinstance(data, dict) and 'info' in data:
            name = data['info'].get('shortName', symbol)
            price_info = data.get('price')
            last_price = "N/A"
            if price_info and isinstance(price_info, list) and len(price_info) > 0:
                 # Get the latest price entry (yfinance hist dicts)
                 last_price_entry = price_info[-1]
                 if 'Close' in last_price_entry:
                     last_price = f"{last_price_entry['Close']:.2f}"
            highlights.append(f"- {name} ({symbol}): Last Price {last_price}")
        elif isinstance(data, dict) and 'error' in data:
             highlights.append(f"- {symbol}: Error fetching data ({data['error']})")
        
    if not highlights:
        return "No specific market data highlights available."
    return "\n".join(highlights)

@app.post("/synthesize", response_model=SynthesisResponse, summary="Synthesize Narrative", description="Generates a natural language response based on query, context, and analysis using an LLM.")
async def synthesize_narrative(request: SynthesisRequest):
    """Endpoint to generate the final narrative.

    Args:
        request: SynthesisRequest containing all necessary data.

    Returns:
        SynthesisResponse containing the generated narrative.

    Raises:
        HTTPException: 500 if synthesis fails or chain not loaded.
    """
    if not chain:
        raise HTTPException(status_code=500, detail="LLM chain not loaded. Check API key and logs.")

    try:
        # Format inputs for the LLM chain
        context_str = format_context(request.retrieved_context)
        analysis_str = format_analysis(request.analysis_results)
        market_str = format_market_data(request.market_data)

        # Invoke the LLM chain asynchronously
        print("Invoking LLM chain...")
        response = await chain.ainvoke({
            "query": request.query,
            "context": context_str,
            "analysis": analysis_str,
            "market_highlights": market_str
        })
        print("LLM response received.")

        # *** Placeholder Response Generation ***
        # response = f"Synthesized response for query: '{request.query}'\n\n"
        # response += f"Analysis Summary:\n{analysis_str}\n\n"
        # response += f"Relevant Information:\n{context_str}\n\n"
        # response += f"Market Data:\n{market_str}"
        # *** End Placeholder ***

        if not response:
             # Handle cases where the LLM might return an empty response
             print("Warning: LLM returned an empty response.")
             raise ValueError("LLM failed to generate a response.")

        return SynthesisResponse(narrative=response)
    except Exception as e:
        print(f"Error during synthesis: {e}")
        import traceback
        traceback.print_exc()
        # Check for specific API errors if using a service like OpenAI
        # if isinstance(e, openai.APIError): ...
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {e}")

if __name__ == "__main__":
    import uvicorn
    # Requires LangChain, langchain-google-genai
    # Set GOOGLE_API_KEY environment variable
    print("Running Language Agent Service. Ensure GOOGLE_API_KEY is set.")
    print(f"Access docs at http://localhost:8004/docs")
    uvicorn.run("agents.language_agent.app:app", host="0.0.0.0", port=8004, reload=True) 