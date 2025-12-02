import httpx 
import json
import logging
from app.models.content import Sentiment
from typing import Tuple, Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Gemini API Configuration (Reads key from settings) ---
GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025"
GEMINI_KEY = settings.GEMINI_API_KEY 
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"

# --- Core LLM Inference Function ---

async def query_gemini(raw_text: str) -> Optional[Dict[str, str]]:
    """
    Makes a single API call to Gemini to perform both summarization and sentiment,
    returning a structured JSON object to be easily parsed.
    """
    
    # 1. Define the System Instruction 
    system_prompt = (
        "You are an AI analyst. Analyze the following text. "
        "Your task is to provide a concise summary (max 2 sentences) and determine the overall sentiment."
    )
    
    # 2. Define the User Query
    user_query = f"Analyze the following content and return only the summary and sentiment: {raw_text}"
    
    # 3. Define the Desired JSON Schema (for structured output)
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "summary": {"type": "STRING", "description": "A single concise sentence summarizing the text."},
            "sentiment": {"type": "STRING", "description": "The determined sentiment, must be either 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'."}
        },
        "required": ["summary", "sentiment"]
    }

    # 4. Construct the full API payload
    payload = {
        "contents": [{ "parts": [{ "text": user_query }] }],
        "systemInstruction": { "parts": [{ "text": system_prompt }] },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # The URL now contains the key read from the environment.
        url = GEMINI_API_URL
        
        try:
            response = await client.post(
                url, 
                headers={'Content-Type': 'application/json'}, 
                json=payload
            )
            response.raise_for_status() 
            
            result = response.json()
            
            # Extract and parse the JSON text part from the candidates block
            json_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')
            
            if json_text:
                return json.loads(json_text)
            else:
                logger.error("Gemini API returned an empty or malformed text response.")
                return None

        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini API call failed. Status: {e.response.status_code}. Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during Gemini API call: {e}")
            return None


# --- Main Analysis Function ---

async def analyze_content(raw_text: str) -> Tuple[Optional[str], Optional[Sentiment]]:
    """
    Performs summarization and sentiment analysis using the Gemini API.
    """
    
    # Call the simplified, structured query function
    structured_data = await query_gemini(raw_text)
    
    summary = None
    sentiment_result = None

    if structured_data and isinstance(structured_data, dict):
        summary = structured_data.get('summary')
        sentiment_label = structured_data.get('sentiment')
        
        if sentiment_label:
            # Map the returned label (e.g., 'POSITIVE') to your SQLAlchemy Enum
            try:
                # Ensure the label is converted to uppercase for the Python Enum check
                sentiment_result = Sentiment[sentiment_label.upper()] 
            except KeyError:
                logger.warning(f"Unknown sentiment label returned: {sentiment_label}")
                
    return summary, sentiment_result