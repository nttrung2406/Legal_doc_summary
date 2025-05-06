from typing import Optional, Dict, Any
from gemini_monitoring import GeminiMonitor
from gemini_metrics import GeminiMetrics
from dotenv import load_dotenv
import os

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
        prompt = f"Please provide a concise summary of the following text:\n\n{text}"
        # Use the original text as reference if none provided
        result = self.monitor.generate_with_metrics(prompt, reference or text)
        
        GeminiMetrics.save_api_call(
            prompt=prompt,
            response=result["text"],
            metrics=result["metrics"],
            latency=result["latency"],
            status=result["status"],
            error=result.get("error"),
            token_usage=result.get("token_usage")
        )
        
        return {
            "summary": result["text"],
            "metrics": result["metrics"],
            "status": result["status"],
            "error": result.get("error")
        }
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """Process a chat message using Gemini with monitoring."""
        result = self.monitor.generate_with_metrics(message)
        
        GeminiMetrics.save_api_call(
            prompt=message,
            response=result["text"],
            metrics=result["metrics"],
            latency=result["latency"],
            status=result["status"],
            error=result.get("error"),
            token_usage=result.get("token_usage")
        )
        
        return {
            "response": result["text"],
            "status": result["status"],
            "error": result.get("error")
        }

gemini_service = GeminiService() 