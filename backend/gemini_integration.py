from typing import Optional, Dict, Any
from gemini_monitoring import (
    api_calls_total,
    api_latency_seconds, api_errors_total, token_usage_total, GeminiMonitor
)
from gemini_metrics import GeminiMetrics
from dotenv import load_dotenv
import os
import time
import logging

logger = logging.getLogger(__name__)
load_dotenv()

class GeminiService:
    def __init__(self):
        """Initialize Gemini service with monitoring."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        self.monitor = GeminiMonitor(api_key=api_key)
    
    async def generate_summary(self, text: str, reference: Optional[str] = None) -> Dict[str, Any]:
        """Generate a summary using Gemini with monitoring."""
        start_time = time.time()
        api_calls_total.inc()
        
        try:
            prompt = f"Please provide a concise summary of the following text:\n\n{text}"
            result = self.monitor.generate_with_metrics(prompt)

            # Update metrics
            latency = time.time() - start_time
            api_latency_seconds.observe(latency)
            
            if result.get("token_usage"):
                token_usage_total.inc(result["token_usage"])
            
            logger.info(f"Generated summary metrics: {result.get('metrics', {})}")
            
            GeminiMetrics.save_api_call(
                prompt=prompt,
                response=result["text"],
                metrics=result.get("metrics", {}),
                latency=latency,
                status=result["status"],
                error=result.get("error"),
                token_usage=result.get("token_usage")
            )
            
            return {
                "summary": result["text"],
                "metrics": result.get("metrics", {}),
                "status": result["status"],
                "error": result.get("error")
            }
        except Exception as e:
            api_errors_total.inc()
            logger.error(f"Error generating summary: {e}")
            raise e
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """Process a chat message using Gemini with monitoring."""
        start_time = time.time()
        api_calls_total.inc()
        
        try:
            result = self.monitor.generate_with_metrics(prompt=message)
            
            # Update metrics
            latency = time.time() - start_time
            api_latency_seconds.observe(latency)
            
            if result.get("token_usage"):
                token_usage_total.inc(result["token_usage"])

            # Log metrics for debugging
            logger.info(f"Chat metrics: {result.get('metrics', {})}")

            GeminiMetrics.save_api_call(
                prompt=message,
                response=result["text"],
                metrics=result.get("metrics", {}),
                latency=latency,
                status=result["status"],
                error=result.get("error"),
                token_usage=result.get("token_usage")
            )
            
            return {
                "response": result["text"],
                "metrics": result.get("metrics", {}),
                "status": result["status"],
                "error": result.get("error")
            }
        except Exception as e:
            api_errors_total.inc()
            logger.error(f"Error in chat: {e}")
            raise e

gemini_service = GeminiService() 