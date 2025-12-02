import httpx 
        import json
        import logging
        import asyncio # Import asyncio
        from app.models.content import Sentiment
        from typing import Tuple, Optional, Dict, Any
        from app.core.config import settings # <--- NEW IMPORT

        logger = logging.getLogger(__name__)

        # --- Gemini API Configuration (Reads key from settings) ---
        GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025"
        GEMINI_KEY = settings.GEMINI_API_KEY 
        GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"

        # --- Core LLM Inference Function ---

        async def query_gemini(raw_text: str) -> Optional[Dict[str, str]]:
            # ... (Function definition remains the same as previously given for Gemini structured output) ...
            
            # 3. Define the Desired JSON Schema
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
                url = GEMINI_API_URL 
                
                # ... (rest of the try/except block remains the same, using the key in the URL)
                try:
                    response = await client.post(
                        url, 
                        headers={'Content-Type': 'application/json'}, 
                        json=payload
                    )
                    response.raise_for_status() 
                    
                    result = response.json()
                    
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

        async def analyze_content(raw_text: str) -> Tuple[Optional[str], Optional[Sentiment]]:
            # ... (analyze_content function remains the same) ...
            structured_data = await query_gemini(raw_text)
            
            summary = None
            sentiment_result = None

            if structured_data and isinstance(structured_data, dict):
                summary = structured_data.get('summary')
                sentiment_label = structured_data.get('sentiment')
                
                if sentiment_label:
                    try:
                        sentiment_result = Sentiment[sentiment_label.upper()] 
                    except KeyError:
                        logger.warning(f"Unknown sentiment label returned: {sentiment_label}")
                        
            return summary, sentiment_result