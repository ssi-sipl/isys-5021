import numpy as np
from typing import List, Dict, Any

class RadarObjectClassifier:
    def __init__(self, initial_rules=None):
        """
        Initialize the radar object classifier with more realistic rules
        """
        # Updated default classification rules with broader, more realistic ranges
        self.default_rules = {
            'person': {
                'range': (1, 100),          # Expanded to 100m detection range
                'velocity': (0.5, 2.5),     # Walking speed range 
                'signal_strength': (0.1, 0.8),  # Broader signal strength range
            },
            'vehicle': {
                'range': (5, 150),          # Extended to 500m for vehicles
                'velocity': (2, 40),        # Broader vehicle speed range
                'signal_strength': (0.4, 1.0),
            }
        }
        
        # Dynamic rules that can be updated based on environment
        self.rules = initial_rules or self.default_rules
        
        # Classification confidence tracking
        self.classification_confidence = {}
    
    def classify_object(self, measurement: Dict[str, Any]) -> str:
        """
        Classify radar object based on current measurement
        
        Args:
            measurement (dict): Current radar measurement
        
        Returns:
            str: Classified object type
        """
        # Probabilistic classification
        classification_scores = {}
        for class_type, rule_set in self.rules.items():
            score = 0
            
            # Scoring mechanism with normalized weights
            # Range check
            if rule_set['range'][0] <= measurement['range'] <= rule_set['range'][1]:
                score += 0.4  # Increased weight for range
            
            # Velocity check
            if rule_set['velocity'][0] <= measurement['velocity'] <= rule_set['velocity'][1]:
                score += 0.3
            
            # Signal strength check
            if rule_set['signal_strength'][0] <= measurement['signal_strength'] <= rule_set['signal_strength'][1]:
                score += 0.3
            
            classification_scores[class_type] = score
        
        # Determine best classification
        if not classification_scores:
            return 'others'
        
        best_class = max(classification_scores, key=classification_scores.get)
        confidence = classification_scores[best_class]
        
        # Store classification confidence
        self.classification_confidence[best_class] = confidence
        
        # If confidence is low, default to 'others'
        return best_class if confidence > 0.5 else 'others'
    
    def update_rules(self, new_measurements: List[Dict[str, Any]], ground_truth: List[str] = None):
        """
        Dynamically adapt classification rules based on new measurements
        
        Args:
            new_measurements (list): Recent radar measurements
            ground_truth (list): Optional ground truth labels for measurements
        """
        if ground_truth:
            for measurement, label in zip(new_measurements, ground_truth):
                # Update rule ranges based on ground truth
                current_rules = self.rules.get(label, {})
                
                # Adaptive rule adjustment with some hysteresis
                current_rules['range'] = (
                    min(current_rules['range'][0], measurement['range']),
                    max(current_rules['range'][1], measurement['range'])
                )
                
                current_rules['velocity'] = (
                    min(current_rules['velocity'][0], measurement['velocity']),
                    max(current_rules['velocity'][1], measurement['velocity'])
                )
                
                self.rules[label] = current_rules

# Example usage
def main():
    # Initialize classifier
    classifier = RadarObjectClassifier()
    
    # Simulated radar measurements
    measurements = [
        {'range': 100, 'velocity': 1.5, 'signal_strength': 0.6},     # Close person
        {'range': 22, 'velocity': 10, 'signal_strength': 0.8},     # Vehicle
        {'range': 150, 'velocity': 1.2, 'signal_strength': 60}     # Person at distance
    ]
    
    # Simulated ground truth (optional)
    ground_truth = ['person', 'vehicle', 'person']
    
    # Classify objects
    for i, measurement in enumerate(measurements):
        classification = classifier.classify_object(measurement)
        print(f"Measurement {i+1}: Range {measurement['range']}m - Classified as {classification}")
        print(f"Confidence: {classifier.classification_confidence.get(classification, 'N/A')}\n")
    
    # Update rules with ground truth
    classifier.update_rules(measurements, ground_truth)

if __name__ == "__main__":
    main()