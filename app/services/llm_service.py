import httpx # A modern, fast, async HTTP client for Python
import json
from app.core.config import settings
from app.models.content import Sentiment
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# --- Hugging Face Model Endpoints ---
# We select two separate, high-quality models for better, specialized results
SUMMARIZATION_MODEL = "facebook/bart-large-cnn" # Excellent for abstractive summarization
SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest" # Optimized for sentiment analysis

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/"

# --- Core LLM Inference Function ---

async def query_model(model_id: str, payload: dict) -> Optional[dict]:
    """
    Makes an asynchronous HTTP POST request to a Hugging Face Inference API endpoint.
    Handles authentication and basic error responses.
    """
    
    # Use httpx for asynchronous requests
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        url = HUGGINGFACE_API_URL + model_id
        
        # Implement Error Handling (Graceful handling if the AI API is down or times out)
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status() # Raise an exception for 4xx or 5xx responses

            result = response.json()
            return result

        except httpx.TimeoutException:
            logger.error(f"Hugging Face API call to {model_id} timed out.")
            return None
        except httpx.HTTPStatusError as e:
            # This handles 4xx (e.g., Auth failure) or 5xx (e.g., Server error)
            logger.error(f"Hugging Face API call to {model_id} failed with status {e.response.status_code}. Response: {e.response.text}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Hugging Face API call to {model_id} returned invalid JSON.")
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
    
    # 2. Sentiment Analysis Task (Classification)
    # The sentiment model takes the full text as input
    sentiment_payload = {"inputs": raw_text}

    # Run both AI calls concurrently (asynchronously)
    summarization_task = query_model(SUMMARIZATION_MODEL, summary_payload)
    sentiment_task = query_model(SENTIMENT_MODEL, sentiment_payload)
    
    results = await httpx.gather(summarization_task, sentiment_task)
    
    summary_result = results[0]
    sentiment_result = results[1]

    # --- Process Summarization Result ---
    summary = None
    if summary_result and isinstance(summary_result, list) and summary_result[0].get('summary_text'):
        # Extract the summary text
        summary = summary_result[0]['summary_text']

    # --- Process Sentiment Result ---
    sentiment = None
    if sentiment_result and isinstance(sentiment_result, list) and sentiment_result[0] and isinstance(sentiment_result[0], list):
        # Hugging Face sentiment models often return a list of labels with scores
        # Example: [[{'label': 'POSITIVE', 'score': 0.99}, {'label': 'NEGATIVE', 'score': 0.005}]]
        
        # Find the label with the highest score
        best_label = None
        highest_score = -1
        
        for classification in sentiment_result[0]:
            score = classification.get('score', 0)
            if score > highest_score:
                highest_score = score
                best_label = classification.get('label')

        if best_label:
            # Map the Hugging Face label to your SQLAlchemy Enum
            try:
                # The labels are usually "POSITIVE", "NEGATIVE", or "NEUTRAL"
                sentiment = Sentiment[best_label.upper()] 
            except KeyError:
                logger.warning(f"Unknown sentiment label returned: {best_label}")


    return summary, sentiment

# Note: We use httpx.gather here instead of asyncio.gather because
# asyncio.gather requires a different setup for the async client.
# httpx is implicitly available via the AsyncClient setup.