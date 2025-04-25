from prometheus_client import Counter, Gauge, Histogram
import time
from typing import Optional, Dict, Any
import google.generativeai as genai
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate.meteor_score import meteor_score
from rouge import Rouge
import nltk

# Download required NLTK data
nltk.download('wordnet')
nltk.download('punkt')

# Initialize Prometheus metrics
rouge_score = Gauge('gemini_rouge_score', 'ROUGE score for Gemini responses')
meteor_score_gauge = Gauge('gemini_meteor_score', 'METEOR score for Gemini responses')
api_calls_total = Counter('gemini_api_calls_total', 'Total number of Gemini API calls', ['status'])
api_latency_seconds = Histogram('gemini_api_latency_seconds', 'Latency of Gemini API calls in seconds')
api_errors_total = Counter('gemini_api_errors_total', 'Total number of Gemini API errors')
token_usage_total = Counter('gemini_token_usage_total', 'Total number of tokens used')

# Initialize Rouge scorer
rouge_scorer = Rouge()

class GeminiMonitor:
    def __init__(self, api_key: str):
        """Initialize Gemini monitoring with API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def _calculate_metrics(self, reference: str, generated: str) -> Dict[str, float]:
        """Calculate ROUGE and METEOR scores between reference and generated text."""
        try:
            # Calculate ROUGE scores
            rouge_scores = rouge_scorer.get_scores(generated, reference)[0]
            rouge_l = rouge_scores['rouge-l']['f']
            
            # Calculate METEOR score
            meteor = meteor_score([reference.split()], generated.split())
            
            return {
                'rouge': rouge_l,
                'meteor': meteor
            }
        except Exception as e:
            print(f"Error calculating metrics: {e}")
            return {
                'rouge': 0.0,
                'meteor': 0.0
            }
    
    def generate_with_metrics(self, prompt: str, reference: Optional[str] = None) -> Dict[str, Any]:
        """Generate text using Gemini and collect metrics."""
        start_time = time.time()
        status = 'success'
        
        try:
            # Make API call
            response = self.model.generate_content(prompt)
            
            # Calculate latency
            latency = time.time() - start_time
            api_latency_seconds.observe(latency)
            
            # Increment API calls counter
            api_calls_total.labels(status=status).inc()
            
            # Get token usage from response
            if hasattr(response, 'usage'):
                token_usage_total.inc(response.usage.total_tokens)
            
            # Calculate metrics if reference is provided
            metrics = {}
            if reference:
                metrics = self._calculate_metrics(reference, response.text)
                rouge_score.set(metrics['rouge'])
                meteor_score_gauge.set(metrics['meteor'])
            
            return {
                'text': response.text,
                'metrics': metrics,
                'latency': latency,
                'status': status
            }
            
        except Exception as e:
            status = 'error'
            api_errors_total.inc()
            api_calls_total.labels(status=status).inc()
            print(f"Error in Gemini API call: {e}")
            return {
                'text': None,
                'metrics': {},
                'latency': time.time() - start_time,
                'status': status,
                'error': str(e)
            }

