import numpy as np
import logging

from typing import Dict, Any, Optional, Final

# Configuration Constants
MAX_HOURS: Final[float] = 160.0
BASE_SCALE: Final[float] = 10.0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import numpy as np
import logging
from typing import Dict, Any, Optional, Final, Tuple

# Configuration Constants
MAX_HOURS: Final[float] = 160.0
BASE_SCALE: Final[float] = 10.0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplexityCalculator:
    """
    Advanced complexity engine using non-linear distribution and 
    weighted geometric normalization.
    """
    
    def __init__(self, weights: Dict[str, Any]):
        # Store the full config dictionary to access the 'weight' sub-key
        if not weights:
            raise ValueError("Weights configuration cannot be empty.")
        self.weights_config = weights
        
    def _apply_non_linear_scaling(self, raw_score: float) -> float:
        """
        Applies an exponential curve to the score. 
        Ensures that a '10' in difficulty feels significantly heavier than a '5'.
        Formula: Result = (Score^1.5)
        """
        return np.power(raw_score, 1.5)

    def calculate_score(self, inputs: Dict[str, float]) -> Tuple[float, float]:
        """
        Calculates a production-grade complexity score.
        
        Args:
            inputs: Raw metric values (0-10 for levels, 0-MAX_HOURS for hours).
            
        Returns:
            Tuple containing (score, margin).
        """
        # 1. Input Sanitization & Filtering
        # Filter inputs based on keys present in the config
        valid_metrics = {
            k: float(v) for k, v in inputs.items() 
            if k in self.weights_config and v is not None
        }
        num_metrics = len(valid_metrics)
        
        if num_metrics == 0:
            return 0.0, 100.0

        # 2. Normalize Hours (Capping at MAX_HOURS)
        # We modify a copy to avoid side effects on the input dict
        processed_values = valid_metrics.copy()
        if "hours" in processed_values:
            raw_hours = processed_values["hours"]
            processed_values["hours"] = min((raw_hours / MAX_HOURS) * BASE_SCALE, BASE_SCALE)

        # 3. Calculate Weighted Linear Base
        values = []
        applied_weights = []
        
        for key, val in processed_values.items():
            values.append(val)
            # Access the 'weight' float inside the config dict
            applied_weights.append(self.weights_config[key]["weight"])

        # Normalize weights in case some metrics are missing (subset calculation)
        weight_sum = sum(applied_weights)
        if weight_sum == 0:
            return 0.0, 100.0
            
        normalized_weights = np.array(applied_weights) / weight_sum
        base_score = np.average(values, weights=normalized_weights)

        # 4. Redistribution (Non-linear Step)
        distributed_score = self._apply_non_linear_scaling(base_score)

        # 5. Error Margin (Logarithmic Penalty)
        total_possible = len(self.weights_config)
        completion_ratio = num_metrics / total_possible
        margin = max(5.0, (1 - np.sqrt(completion_ratio)) * 100)

        return round(float(distributed_score), 2), round(float(margin), 2)
    