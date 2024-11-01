import json

class FormatValidator:
    def is_valid(self, assessment: str) -> bool:
        """
        Validate if the assessment follows the required format.
        """
        try:
            if isinstance(assessment, str):
                assessment = json.loads(assessment)
            
            # check required fields
            required_fields = ['score', 'reason', 'confidence']
            if not all(field in assessment for field in required_fields):
                return False
            
            # validate score range
            if not (0 <= assessment['score'] <= 100):
                return False
                
            # validate confidence range
            if not (0 <= assessment['confidence'] <= 1):
                return False
                
            # validate reason is non-empty string
            if not isinstance(assessment['reason'], str) or not assessment['reason'].strip():
                return False
                
            return True
            
        except (json.JSONDecodeError, TypeError, KeyError):
            return False