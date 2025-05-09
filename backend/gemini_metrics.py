from pymongo import MongoClient
import os
from datetime import datetime
from typing import Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.legal_doc_db
gemini_metrics = db.gemini_metrics

class GeminiMetrics:
    @staticmethod
    def save_api_call(
        prompt: str,
        response: str,
        metrics: Dict[str, float],
        latency: float,
        status: str,
        error: Optional[str] = None,
        token_usage: Optional[int] = None
    ):
        """Save a Gemini API call and its metrics to MongoDB."""
        try:
            document = {
                "timestamp": datetime.utcnow(),
                "prompt": prompt,
                "response": response,
                "metrics": metrics,
                "latency": latency,
                "status": status,
                "token_usage": token_usage,
                "error": error,
                # Add evaluation metrics
                "relevance_score": metrics.get('relevance', 0),
                "accuracy_score": metrics.get('accuracy', 0),
                "completeness_score": metrics.get('completeness', 0),
                "toxicity_score": metrics.get('toxicity', 0),
                "factuality_score": metrics.get('factuality', 0),
                "grammar_score": metrics.get('grammar', 0)
            }
            gemini_metrics.insert_one(document)
            logger.info(f"Saved metrics to MongoDB: {metrics}")
        except Exception as e:
            logger.error(f"Error saving metrics to MongoDB: {e}")

    @staticmethod
    def get_recent_metrics(limit: int = 100) -> list:
        """Get recent metrics from MongoDB."""
        try:
            return list(gemini_metrics.find().sort("timestamp", -1).limit(limit))
        except Exception as e:
            logger.error(f"Error retrieving metrics from MongoDB: {e}")
            return []

    @staticmethod
    def get_metrics_summary() -> Dict[str, Any]:
        """Get summary statistics of metrics."""
        try:
            total_calls = gemini_metrics.count_documents({})
            success_calls = gemini_metrics.count_documents({"status": "success"})
            
            # Calculate average scores
            avg_scores = gemini_metrics.aggregate([
                {
                    "$group": {
                        "_id": None,
                        "avg_relevance": {"$avg": "$relevance_score"},
                        "avg_accuracy": {"$avg": "$accuracy_score"},
                        "avg_completeness": {"$avg": "$completeness_score"},
                        "avg_toxicity": {"$avg": "$toxicity_score"},
                        "avg_factuality": {"$avg": "$factuality_score"},
                        "avg_grammar": {"$avg": "$grammar_score"},
                        "avg_latency": {"$avg": "$latency"}
                    }
                }
            ]).next()
            
            return {
                "total_calls": total_calls,
                "success_rate": success_calls / total_calls if total_calls > 0 else 0,
                "average_latency": avg_scores["avg_latency"],
                "average_scores": {
                    "relevance": avg_scores["avg_relevance"],
                    "accuracy": avg_scores["avg_accuracy"],
                    "completeness": avg_scores["avg_completeness"],
                    "toxicity": avg_scores["avg_toxicity"],
                    "factuality": avg_scores["avg_factuality"],
                    "grammar": avg_scores["avg_grammar"]
                }
            }
        except Exception as e:
            logger.error(f"Error calculating metrics summary: {e}")
            return {
                "total_calls": 0,
                "success_rate": 0,
                "average_latency": 0,
                "average_scores": {
                    "relevance": 0,
                    "accuracy": 0,
                    "completeness": 0,
                    "toxicity": 0,
                    "factuality": 0,
                    "grammar": 0
                }
            } 