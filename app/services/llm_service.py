import httpx 
import json
import asyncio 
import logging
from app.core.config import settings
from app.models.content import Sentiment
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# --- Hugging Face Model Endpoints (FINAL ATTEMPT: Use a single, reliable model) ---
# Use a simple, non-specialized text model and ask it to perform both tasks.
GENERATION_MODEL = "distilbert-base-uncased" 

HUGGINGFACE_API_URL = "https://router.huggingface.co/models/" 

# --- Core LLM Inference Function ---

async def query_model(model_id: str, payload: dict) -> Optional[dict]:
    """
    Makes an asynchronous HTTP POST request to a Hugging Face Inference API endpoint.
    """
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # NOTE: Hugging Face uses 'Authorization' header for authentication
        headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        url = HUGGINGFACE_API_URL + model_id
        
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status() 

            result = response.json()
            return result

        except httpx.TimeoutException:
            logger.error(f"LLM API call to {model_id} timed out after 15s. (Network Error/Slow Model)")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API call to {model_id} failed. Status: {e.response.status_code}. Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during API call to {model_id}: {e}")
            return None


# --- Main Analysis Function ---

async def analyze_content(raw_text: str) -> Tuple[Optional[str], Optional[Sentiment]]:
    """
    Performs summarization and basic sentiment analysis using a single model query.
    """
    
    # CRITICAL: Ask the model to perform both tasks and return a structured format
    prompt = (
        f"Analyze the following text. "
        f"1. Provide a 3-sentence summary. "
        f"2. Determine the overall sentiment (Positive, Negative, or Neutral). "
        f"Text: '{raw_text}'"
    )
    
    payload = {
        "inputs": prompt, 
        "parameters": {
            "max_new_tokens": 100, 
            "return_full_text": False
        }
    }

    # Use only one model to simplify the network logic
    result = await query_model(GENERATION_MODEL, payload)
    
    if not result or not isinstance(result, list) or not result[0].get('generated_text'):
        logger.error("LLM returned an empty or invalid response structure.")
        return None, None

    generated_text = result[0]['generated_text'].strip()

    # Simple logic to extract Summary and Sentiment from the unstructured text output
    summary_text = generated_text # Assume the entire output is the summary
    sentiment_result = None

    # Simple keyword detection for sentiment (since the prompt asks for it)
    lower_text = generated_text.lower()
    if 'positive' in lower_text or 'good' in lower_text:
        sentiment_result = Sentiment.POSITIVE
    elif 'negative' in lower_text or 'bad' in lower_text:
        sentiment_result = Sentiment.NEGATIVE
    else:
        sentiment_result = Sentiment.NEUTRAL

    return summary_text, sentiment_result