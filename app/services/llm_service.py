import httpx 
import json
import asyncio 
import logging
from app.core.config import settings
from app.models.content import Sentiment
from typing import Tuple, Optional, List, Dict

logger = logging.getLogger(__name__)

# --- Hugging Face Model Endpoints (Using the last known good URL) ---
SUMMARIZATION_MODEL = "facebook/bart-large-cnn"
SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english" 

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/" # We MUST use this base URL

# --- Core LLM Inference Function ---

async def query_model(model_id: str, payload: Dict, is_sentiment: bool) -> Optional[List[Dict]]:
    """
    Makes an asynchronous HTTP POST request to a Hugging Face Inference API endpoint.
    """
    
    # NOTE: Reverting to the old api-inference URL because the router one is path sensitive
    # and requires a different structure that often conflicts with generic model calls.
    url = f"https://api-inference.huggingface.co/models/{model_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # NOTE: Hugging Face uses 'Authorization' header for authentication
        headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            # For sentiment, the input should be wrapped in 'inputs' structure: {"inputs": ["text"]}
            if is_sentiment:
                request_payload = {"inputs": [payload["inputs"]]}
            else:
                # For summarization, structure depends on the model, but simple inputs usually work
                request_payload = payload

            response = await client.post(url, headers=headers, json=request_payload)
            response.raise_for_status() 

            result = response.json()
            # If the response is a nested list (common for multi-label classification), simplify it
            if is_sentiment and result and isinstance(result, list) and isinstance(result[0], list):
                 return result[0]
            
            return result

        except httpx.TimeoutException:
            logger.error(f"LLM API call to {model_id} timed out after 30s.")
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
    Performs summarization and sentiment analysis on the raw text concurrently.
    """
    
    # 1. Summarization Task
    summary_payload = {"inputs": raw_text, "parameters": {"min_length": 30, "max_length": 150}}
    
    # 2. Sentiment Analysis Task
    sentiment_payload = {"inputs": raw_text}

    # Run both AI calls concurrently (asynchronously)
    summarization_task = query_model(SUMMARIZATION_MODEL, summary_payload, is_sentiment=False)
    sentiment_task = query_model(SENTIMENT_MODEL, sentiment_payload, is_sentiment=True)
    
    # We use asyncio.gather for true concurrency
    results = await asyncio.gather(summarization_task, sentiment_task)
    
    summary_result: Optional[List[Dict]] = results[0]
    sentiment_result: Optional[List[Dict]] = results[1]

    # --- Process Summarization Result ---
    summary = None
    # Check for the expected list structure from summarization model
    if summary_result and isinstance(summary_result, list) and summary_result[0].get('summary_text'):
        summary = summary_result[0]['summary_text']

    # --- Process Sentiment Result ---
    sentiment = None
    if sentiment_result and isinstance(sentiment_result, list):
        # Find the label with the highest score
        best_label = None
        highest_score = -1
        
        for classification in sentiment_result:
            score = classification.get('score', 0)
            if score > highest_score:
                highest_score = score
                best_label = classification.get('label')

        if best_label:
            # Map the Hugging Face label (e.g., 'POSITIVE') to your SQLAlchemy Enum
            try:
                # DistilBERT sentiment labels are usually 'POSITIVE' or 'NEGATIVE'
                sentiment = Sentiment[best_label.upper()] 
            except KeyError:
                logger.warning(f"Unknown sentiment label returned: {best_label}")


    return summary, sentiment