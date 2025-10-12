"""
Input validation utilities for scenario builder.
"""

from typing import Dict, List, Tuple, Any


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class ScenarioValidator:
    """Validator for scenario configuration inputs."""
    
    @staticmethod
    def validate_positive_int(value: str, field_name: str) -> int:
        """Validate positive integer."""
        try:
            val = int(value)
            if val <= 0:
                raise ValidationError(f"{field_name} must be positive, got {val}")
            return val
        except ValueError:
            raise ValidationError(f"{field_name} must be an integer, got '{value}'")
    
    @staticmethod
    def validate_non_negative_int(value: str, field_name: str) -> int:
        """Validate non-negative integer."""
        try:
            val = int(value)
            if val < 0:
                raise ValidationError(f"{field_name} must be non-negative, got {val}")
            return val
        except ValueError:
            raise ValidationError(f"{field_name} must be an integer, got '{value}'")
    
    @staticmethod
    def validate_positive_float(value: str, field_name: str) -> float:
        """Validate positive float."""
        try:
            val = float(value)
            if val <= 0:
                raise ValidationError(f"{field_name} must be positive, got {val}")
            return val
        except ValueError:
            raise ValidationError(f"{field_name} must be a number, got '{value}'")
    
    @staticmethod
    def validate_non_negative_float(value: str, field_name: str) -> float:
        """Validate non-negative float."""
        try:
            val = float(value)
            if val < 0:
                raise ValidationError(f"{field_name} must be non-negative, got {val}")
            return val
        except ValueError:
            raise ValidationError(f"{field_name} must be a number, got '{value}'")
    
    @staticmethod
    def validate_range_float(value: str, field_name: str, min_val: float, max_val: float) -> float:
        """Validate float within range."""
        try:
            val = float(value)
            if not (min_val <= val <= max_val):
                raise ValidationError(f"{field_name} must be between {min_val} and {max_val}, got {val}")
            return val
        except ValueError:
            raise ValidationError(f"{field_name} must be a number, got '{value}'")
    
    @staticmethod
    def validate_string(value: str, field_name: str) -> str:
        """Validate non-empty string."""
        val = value.strip()
        if not val:
            raise ValidationError(f"{field_name} cannot be empty")
        return val
    
    @staticmethod
    def validate_inventory_list(value: str, field_name: str) -> List[int]:
        """Validate comma-separated list of integers."""
        val = value.strip()
        if not val:
            raise ValidationError(f"{field_name} cannot be empty")
        
        try:
            # Try parsing as single int first
            return [int(val)]
        except ValueError:
            # Try parsing as comma-separated list
            try:
                parts = [p.strip() for p in val.split(',')]
                return [int(p) for p in parts if p]
            except ValueError:
                raise ValidationError(f"{field_name} must be an integer or comma-separated list of integers")
    
    @staticmethod
    def validate_utility_weights(utilities: List[Dict[str, Any]]) -> None:
        """Validate that utility weights sum to 1.0."""
        if not utilities:
            raise ValidationError("At least one utility function must be defined")
        
        total_weight = sum(u['weight'] for u in utilities)
        if abs(total_weight - 1.0) > 1e-6:
            raise ValidationError(f"Utility weights must sum to 1.0, got {total_weight:.6f}")
    
    @staticmethod
    def validate_ces_params(params: Dict[str, float]) -> None:
        """Validate CES utility parameters."""
        if 'rho' not in params:
            raise ValidationError("CES utility requires 'rho' parameter")
        if 'wA' not in params or 'wB' not in params:
            raise ValidationError("CES utility requires 'wA' and 'wB' parameters")
        
        if params['rho'] == 1.0:
            raise ValidationError("CES utility cannot have rho=1.0")
        if params['wA'] <= 0 or params['wB'] <= 0:
            raise ValidationError("CES weights must be positive")
    
    @staticmethod
    def validate_linear_params(params: Dict[str, float]) -> None:
        """Validate linear utility parameters."""
        if 'vA' not in params or 'vB' not in params:
            raise ValidationError("Linear utility requires 'vA' and 'vB' parameters")
        
        if params['vA'] <= 0 or params['vB'] <= 0:
            raise ValidationError("Linear utility values must be positive")

