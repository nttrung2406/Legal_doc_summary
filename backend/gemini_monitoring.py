from prometheus_client import Counter, Gauge, Histogram
import time
from typing import Optional, Dict, Any
import google.generativeai as genai
import logging
import json

logger = logging.getLogger(__name__)

# Initialize metrics
relevance_score = Gauge('gemini_relevance_score', 'Relevance score (1-10) for Gemini responses')
accuracy_score = Gauge('gemini_accuracy_score', 'Accuracy score (1-10) for Gemini responses')
completeness_score = Gauge('gemini_completeness_score', 'Completeness score (1-10) for Gemini responses')
toxicity_score = Gauge('gemini_toxicity_score', 'Toxicity score (1-10) for Gemini responses')
factuality_score = Gauge('gemini_factuality_score', 'Factuality score (1-10) for Gemini responses')
grammar_score = Gauge('gemini_grammar_score', 'Grammar & fluency score (1-10) for Gemini responses')
api_calls_total = Counter('gemini_api_calls_total', 'Total number of Gemini API calls', ['status'])
api_latency_seconds = Histogram('gemini_api_latency_seconds', 'Latency of Gemini API calls in seconds')
api_errors_total = Counter('gemini_api_errors_total', 'Total number of Gemini API errors')
token_usage_total = Counter('gemini_token_usage_total', 'Total number of tokens used')

class GeminiMonitor:
    def __init__(self, api_key: str):
        """Initialize Gemini monitoring with API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def _evaluate_response(self, text: str) -> Dict[str, float]:
        """Use Gemini to evaluate its own response."""
        try:
            if not text or not isinstance(text, str):
                logger.error("Invalid text for evaluation")
                return self._get_default_scores()

            evaluation_prompt = f"""Evaluate this response based on the following criteria. Rate each from 1 to 10:

Response to evaluate:
{text}

Please provide scores for:
1. Relevance (how well it addresses the topic)
2. Accuracy (how correct the information is)
3. Completeness (how thorough the response is)
4. Toxicity (how harmful or inappropriate the content is)
5. Factuality (how factual and well-supported the claims are)
6. Grammar & fluency (how well-written and clear the text is)

Provide the scores in JSON format like this:
{{
    "relevance": 8,
    "accuracy": 7,
    "completeness": 9,
    "toxicity": 1,
    "factuality": 8,
    "grammar": 9
}}"""

            evaluation = self.model.generate_content(evaluation_prompt)

            try:
                # Extract JSON from the response
                scores = json.loads(evaluation.text)
                
                # Update Prometheus metrics
                relevance_score.set(scores.get('relevance', 0))
                accuracy_score.set(scores.get('accuracy', 0))
                completeness_score.set(scores.get('completeness', 0))
                toxicity_score.set(scores.get('toxicity', 0))
                factuality_score.set(scores.get('factuality', 0))
                grammar_score.set(scores.get('grammar', 0))
                
                logger.info(f"Evaluation scores: {scores}")
                return scores
                
            except json.JSONDecodeError:
                logger.error("Failed to parse evaluation scores as JSON")
                return self._get_default_scores()
                
        except Exception as e:
            logger.error(f"Error in self-evaluation: {str(e)}")
            return self._get_default_scores()
    
    def _get_default_scores(self) -> Dict[str, float]:
        """Return default scores when evaluation fails."""
        return {
            'relevance': 0.0,
            'accuracy': 0.0,
            'completeness': 0.0,
            'toxicity': 0.0,
            'factuality': 0.0,
            'grammar': 0.0
        }
    
    def generate_with_metrics(self, prompt: str, reference: Optional[str] = None) -> Dict[str, Any]:
        """Generate text using Gemini and collect metrics."""
        start_time = time.time()
        status = 'success'
        
        try:
            response = self.model.generate_content(prompt)
            
            latency = time.time() - start_time
            api_latency_seconds.observe(latency)
            api_calls_total.labels(status=status).inc()
            
            evaluation_scores = self._evaluate_response(response.text)
            
            # Update Prometheus gauges
            relevance_score.set(evaluation_scores.get('relevance', 0))
            accuracy_score.set(evaluation_scores.get('accuracy', 0))
            completeness_score.set(evaluation_scores.get('completeness', 0))
            toxicity_score.set(evaluation_scores.get('toxicity', 0))
            factuality_score.set(evaluation_scores.get('factuality', 0))
            grammar_score.set(evaluation_scores.get('grammar', 0))
            
            logger.info(f"Updated metrics: {evaluation_scores}")
            
            return {
                'text': response.text,
                'metrics': evaluation_scores,
                'latency': latency,
                'status': status,
                'token_usage': getattr(response.usage, 'total_tokens', None) if hasattr(response, 'usage') else None
            }
        except Exception as e:
            status = 'error'
            api_errors_total.inc()
            api_calls_total.labels(status=status).inc()
            logger.error(f"Error in Gemini API call: {str(e)}")
            return {
                'text': None,
                'metrics': self._get_default_scores(),
                'latency': time.time() - start_time,
                'status': status,
                'error': str(e)
            }

