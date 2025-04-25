from pymongo import MongoClient
import os
from datetime import datetime
from typing import Dict, Any, Optional
import time

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
                "error": error
            }
            gemini_metrics.insert_one(document)
        except Exception as e:
            print(f"Error saving metrics to MongoDB: {e}")

    @staticmethod
    def get_recent_metrics(limit: int = 100) -> list:
        """Get recent metrics from MongoDB."""
        try:
            return list(gemini_metrics.find().sort("timestamp", -1).limit(limit))
        except Exception as e:
            print(f"Error retrieving metrics from MongoDB: {e}")
            return []

    @staticmethod
    def get_metrics_summary() -> Dict[str, Any]:
        """Get summary statistics of metrics."""
        try:

            total_calls = gemini_metrics.count_documents({})

            success_calls = gemini_metrics.count_documents({"status": "success"})

            avg_latency = gemini_metrics.aggregate([
                {"$group": {"_id": None, "avg": {"$avg": "$latency"}}}
            ]).next()["avg"]

            avg_rouge = gemini_metrics.aggregate([
                {"$match": {"metrics.rouge": {"$exists": True}}},
                {"$group": {"_id": None, "avg": {"$avg": "$metrics.rouge"}}}
            ]).next()["avg"]

            avg_meteor = gemini_metrics.aggregate([
                {"$match": {"metrics.meteor": {"$exists": True}}},
                {"$group": {"_id": None, "avg": {"$avg": "$metrics.meteor"}}}
            ]).next()["avg"]
            
            return {
                "total_calls": total_calls,
                "success_rate": success_calls / total_calls if total_calls > 0 else 0,
                "average_latency": avg_latency,
                "average_rouge": avg_rouge,
                "average_meteor": avg_meteor
            }
        except Exception as e:
            print(f"Error calculating metrics summary: {e}")
            return {
                "total_calls": 0,
                "success_rate": 0,
                "average_latency": 0,
                "average_rouge": 0,
                "average_meteor": 0
            } 