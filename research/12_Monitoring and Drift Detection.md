
# 12. Monitoring and Drift Detection
monitoring_module = """\"\"\"
Monitoring, Drift Detection, and Alerting
\"\"\"

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import redis
import pickle

logger = logging.getLogger(__name__)


@dataclass
class DriftReport:
    feature_name: str
    drift_detected: bool
    p_value: float
    statistic: float
    threshold: float
    sample_size: int
    timestamp: str


class DataDriftDetector:
    \"\"\"Detect data drift using statistical tests\"\"\"
    
    def __init__(
        self,
        reference_data: np.ndarray,
        psi_threshold: float = 0.2,
        ks_threshold: float = 0.05
    ):
        self.reference_data = reference_data
        self.psi_threshold = psi_threshold
        self.ks_threshold = ks_threshold
        self.reference_distribution = self._calculate_distribution(reference_data)
    
    def _calculate_distribution(self, data: np.ndarray, bins: int = 10) -> np.ndarray:
        \"\"\"Calculate histogram distribution\"\"\"
        hist, _ = np.histogram(data, bins=bins, range=(data.min(), data.max()), density=True)
        return hist + 1e-10  # Add small epsilon to avoid division by zero
    
    def calculate_psi(
        self,
        current_data: np.ndarray,
        bins: int = 10
    ) -> Tuple[float, bool]:
        \"\"\"Calculate Population Stability Index\"\"\"
        current_dist = self._calculate_distribution(current_data, bins)
        
        # Calculate PSI
        psi = np.sum((current_dist - self.reference_distribution) * 
                     np.log(current_dist / self.reference_distribution))
        
        drift_detected = psi > self.psi_threshold
        return psi, drift_detected
    
    def kolmogorov_smirnov_test(
        self,
        current_data: np.ndarray
    ) -> Tuple[float, float, bool]:
        \"\"\"Perform KS test\"\"\"
        statistic, p_value = stats.ks_2samp(self.reference_data, current_data)
        drift_detected = p_value < self.ks_threshold
        return statistic, p_value, drift_detected
    
    def wasserstein_distance(self, current_data: np.ndarray) -> float:
        \"\"\"Calculate Wasserstein distance\"\"\"
        return stats.wasserstein_distance(self.reference_data, current_data)
    
    def detect_drift(self, current_data: np.ndarray) -> DriftReport:
        \"\"\"Run all drift detection methods\"\"\"
        ks_stat, ks_pvalue, ks_drift = self.kolmogorov_smirnov_test(current_data)
        psi, psi_drift = self.calculate_psi(current_data)
        
        # Combined drift detection
        drift_detected = ks_drift or psi_drift
        
        return DriftReport(
            feature_name="image_features",
            drift_detected=drift_detected,
            p_value=ks_pvalue,
            statistic=ks_stat,
            threshold=self.ks_threshold,
            sample_size=len(current_data),
            timestamp=datetime.now().isoformat()
        )


class ModelPerformanceMonitor:
    \"\"\"Monitor model performance over time\"\"\"
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.predictions = []
        self.ground_truths = []
        self.confidences = []
        self.timestamps = []
    
    def add_prediction(
        self,
        prediction: int,
        ground_truth: int,
        confidence: float
    ):
        \"\"\"Add a new prediction\"\"\"
        self.predictions.append(prediction)
        self.ground_truths.append(ground_truth)
        self.confidences.append(confidence)
        self.timestamps.append(datetime.now())
        
        # Maintain window size
        if len(self.predictions) > self.window_size:
            self.predictions.pop(0)
            self.ground_truths.pop(0)
            self.confidences.pop(0)
            self.timestamps.pop(0)
    
    def get_metrics(self) -> Dict[str, float]:
        \"\"\"Calculate current metrics\"\"\"
        if len(self.predictions) == 0:
            return {}
        
        predictions = np.array(self.predictions)
        ground_truths = np.array(self.ground_truths)
        confidences = np.array(self.confidences)
        
        accuracy = np.mean(predictions == ground_truths)
        avg_confidence = np.mean(confidences)
        
        # Confidence calibration
        confidence_bins = np.digitize(confidences, np.arange(0, 1.1, 0.1))
        calibration_error = 0
        
        for bin_id in range(1, 11):
            mask = confidence_bins == bin_id
            if np.sum(mask) > 0:
                bin_acc = np.mean(predictions[mask] == ground_truths[mask])
                bin_conf = np.mean(confidences[mask])
                calibration_error += np.abs(bin_acc - bin_conf) * np.sum(mask)
        
        calibration_error /= len(predictions)
        
        return {
            'accuracy': accuracy,
            'avg_confidence': avg_confidence,
            'calibration_error': calibration_error,
            'sample_count': len(predictions)
        }
    
    def check_performance_degradation(
        self,
        baseline_accuracy: float,
        threshold: float = 0.05
    ) -> bool:
        \"\"\"Check if performance has degraded\"\"\"
        current_metrics = self.get_metrics()
        if not current_metrics:
            return False
        
        current_accuracy = current_metrics['accuracy']
        degradation = baseline_accuracy - current_accuracy
        
        return degradation > threshold


class FeatureDriftMonitor:
    \"\"\"Monitor feature drift in embedding space\"\"\"
    
    def __init__(self, reference_embeddings: np.ndarray):
        self.reference_mean = np.mean(reference_embeddings, axis=0)
        self.reference_std = np.std(reference_embeddings, axis=0)
        self.reference_cov = np.cov(reference_embeddings.T)
    
    def calculate_mahalanobis_distance(
        self,
        embeddings: np.ndarray
    ) -> np.ndarray:
        \"\"\"Calculate Mahalanobis distance from reference distribution\"\"\"
        try:
            inv_cov = np.linalg.inv(self.reference_cov)
            diff = embeddings - self.reference_mean
            distances = np.sqrt(np.sum(diff @ inv_cov * diff, axis=1))
            return distances
        except:
            # Fallback to Euclidean distance
            return np.linalg.norm(embeddings - self.reference_mean, axis=1)
    
    def detect_outliers(
        self,
        embeddings: np.ndarray,
        threshold: float = 3.0
    ) -> Tuple[np.ndarray, float]:
        \"\"\"Detect outlier samples\"\"\"
        distances = self.calculate_mahalanobis_distance(embeddings)
        outlier_ratio = np.mean(distances > threshold)
        return distances, outlier_ratio


class MonitoringDashboard:
    \"\"\"Simple monitoring dashboard backend\"\"\"
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        try:
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            self.redis_client.ping()
        except:
            self.redis_client = None
            logger.warning("Redis not available, using in-memory storage")
            self._memory_store = {}
    
    def log_metric(self, key: str, value: float, timestamp: Optional[str] = None):
        \"\"\"Log a metric\"\"\"
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        data = {'value': value, 'timestamp': timestamp}
        
        if self.redis_client:
            self.redis_client.lpush(f"metrics:{key}", json.dumps(data))
            self.redis_client.ltrim(f"metrics:{key}", 0, 9999)  # Keep last 10000
        else:
            if key not in self._memory_store:
                self._memory_store[key] = []
            self._memory_store[key].append(data)
    
    def get_metrics(self, key: str, hours: int = 24) -> List[Dict]:
        \"\"\"Get metrics for last N hours\"\"\"
        cutoff = datetime.now() - timedelta(hours=hours)
        
        if self.redis_client:
            data = self.redis_client.lrange(f"metrics:{key}", 0, -1)
            metrics = [json.loads(d) for d in data]
        else:
            metrics = self._memory_store.get(key, [])
        
        return [
            m for m in metrics 
            if datetime.fromisoformat(m['timestamp']) > cutoff
        ]
    
    def log_prediction(
        self,
        prediction: str,
        confidence: float,
        latency_ms: float,
        model_version: str
    ):
        \"\"\"Log a prediction event\"\"\"
        data = {
            'prediction': prediction,
            'confidence': confidence,
            'latency_ms': latency_ms,
            'model_version': model_version,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.redis_client:
            self.redis_client.lpush("predictions", json.dumps(data))
        else:
            if 'predictions' not in self._memory_store:
                self._memory_store['predictions'] = []
            self._memory_store['predictions'].append(data)


class AlertManager:
    \"\"\"Alert management system\"\"\"
    
    def __init__(self):
        self.alerts = []
        self.alert_handlers = []
    
    def add_handler(self, handler):
        \"\"\"Add an alert handler\"\"\"
        self.alert_handlers.append(handler)
    
    def trigger_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        \"\"\"Trigger an alert\"\"\"
        alert = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        self.alerts.append(alert)
        
        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    def check_drift_alert(self, drift_report: DriftReport):
        \"\"\"Check if drift alert should be triggered\"\"\"
        if drift_report.drift_detected:
            self.trigger_alert(
                'data_drift',
                f"Data drift detected: {drift_report.feature_name} "
                f"(p-value: {drift_report.p_value:.4f})",
                'critical' if drift_report.p_value < 0.01 else 'warning'
            )
    
    def check_performance_alert(self, metrics: Dict[str, float], baseline: Dict[str, float]):
        \"\"\"Check if performance alert should be triggered\"\"\"
        if 'accuracy' in metrics and 'accuracy' in baseline:
            acc_drop = baseline['accuracy'] - metrics['accuracy']
            if acc_drop > 0.1:
                self.trigger_alert(
                    'performance_degradation',
                    f"Accuracy dropped by {acc_drop:.2%}",
                    'critical'
                )
            elif acc_drop > 0.05:
                self.trigger_alert(
                    'performance_degradation',
                    f"Accuracy dropped by {acc_drop:.2%}",
                    'warning'
                )


# Slack alert handler example
def slack_alert_handler(webhook_url: str):
    \"\"\"Create Slack alert handler\"\"\"
    import requests
    
    def handler(alert: Dict):
        color = {'critical': 'danger', 'warning': 'warning', 'info': 'good'}.get(
            alert['severity'], 'warning'
        )
        
        payload = {
            "attachments": [{
                "color": color,
                "title": f"🚨 MLOps Alert: {alert['type']}",
                "text": alert['message'],
                "footer": "CNN MLOps Platform",
                "ts": datetime.now().timestamp()
            }]
        }
        
        try:
            requests.post(webhook_url, json=payload)
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    return handler
"""

with open(f"{project_root}/src/monitoring/drift_detector.py", "w") as f:
    f.write(monitoring_module)

print("✅ Monitoring and drift detection module created")
