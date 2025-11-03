"""
Central configuration for Decimal precision in VMT simulation.

This module defines global parameters for fixed-precision decimal arithmetic
used throughout the simulation engine to ensure determinism and prevent
floating-point errors in economic computations.

Usage:
    from vmt_engine.core.decimal_config import quantize_quantity, DECIMAL_PRECISION
    
    value = quantize_quantity(Decimal("123.456789"))
    assert value == Decimal("123.46")  # Assuming 2 decimal places
"""

from decimal import Decimal, getcontext, ROUND_HALF_UP

# ============================================================================
# Precision Configuration
# ============================================================================

# Global precision for Decimal context (total number of significant digits)
DECIMAL_PRECISION = 28

# Number of decimal places for quantity values
# This controls the smallest unit of trade: 10^-QUANTITY_DECIMAL_PLACES
QUANTITY_DECIMAL_PLACES = 4

# Quantization exponent (10^-QUANTITY_DECIMAL_PLACES)
QUANTITY_QUANTIZER = Decimal("0." + "0" * (QUANTITY_DECIMAL_PLACES - 1) + "1")

# Rounding mode for quantities
DECIMAL_ROUNDING = ROUND_HALF_UP

# ============================================================================
# Context Initialization
# ============================================================================

def _initialize_decimal_context():
    """Initialize the global Decimal context with our precision settings."""
    ctx = getcontext()
    ctx.prec = DECIMAL_PRECISION
    ctx.rounding = DECIMAL_ROUNDING

# Initialize on import
_initialize_decimal_context()

# ============================================================================
# Helper Functions
# ============================================================================

def quantize_quantity(value: Decimal) -> Decimal:
    """
    Quantize a Decimal value to the configured number of decimal places.
    
    This function enforces canonical representation of quantities throughout
    the simulation, ensuring all values conform to the same precision.
    
    Args:
        value: A Decimal value to quantize
        
    Returns:
        A Decimal value rounded to QUANTITY_DECIMAL_PLACES decimal places
        
    Examples:
        >>> quantize_quantity(Decimal("123.456789"))
        Decimal('123.4568')  # Rounded to 4 decimal places
        >>> quantize_quantity(Decimal("10"))
        Decimal('10.0000')
    """
    return value.quantize(QUANTITY_QUANTIZER, rounding=DECIMAL_ROUNDING)


def decimal_from_numeric(value: int | float) -> Decimal:
    """
    Convert an int or float to Decimal, avoiding binary float artifacts.
    
    This function should be used whenever converting numeric literals or
    external data to Decimal to ensure precision preservation.
    
    Args:
        value: An integer or float value
        
    Returns:
        A Decimal value quantized to the configured precision
        
    Examples:
        >>> decimal_from_numeric(42)
        Decimal('42.0000')
        >>> decimal_from_numeric(0.123456789)
        Decimal('0.1235')  # Rounded to 4 decimal places
    """
    # Convert via string to avoid floating-point binary artifacts
    if isinstance(value, int):
        # For integers, create Decimal directly for efficiency
        dec = Decimal(value)
    else:
        # For floats, convert via string to preserve precision
        dec = Decimal(str(value))
    
    return quantize_quantity(dec)


def to_storage_int(value: Decimal) -> int:
    """
    Convert a Decimal quantity to integer for storage.
    
    Multiplies by 10^QUANTITY_DECIMAL_PLACES to store fractional parts as integers.
    Use this when serializing to INTEGER database columns.
    
    Args:
        value: A Decimal quantity value
        
    Returns:
        Integer representation: value * 10^QUANTITY_DECIMAL_PLACES
        
    Examples:
        >>> to_storage_int(Decimal('5.1234'))
        51234  # Stores as thousandths (4 decimal places)
        >>> to_storage_int(Decimal('10'))
        100000  # Stores as 100000 minor units
    """
    multiplier = Decimal('10') ** QUANTITY_DECIMAL_PLACES
    return int(value * multiplier)


def from_storage_int(value: int) -> Decimal:
    """
    Convert stored integer back to Decimal quantity.
    
    Divides by 10^QUANTITY_DECIMAL_PLACES to recover the original decimal value.
    Use this when deserializing from INTEGER database columns.
    
    Args:
        value: Stored integer value
        
    Returns:
        Decimal quantity value
        
    Examples:
        >>> from_storage_int(51234)
        Decimal('5.1234')
        >>> from_storage_int(100000)
        Decimal('10.0000')
    """
    divisor = Decimal('10') ** QUANTITY_DECIMAL_PLACES
    return quantize_quantity(Decimal(value) / divisor)


# ============================================================================
# Validation
# ============================================================================

def validate_decimal_config():
    """
    Validate that decimal configuration parameters are consistent.
    
    This function checks for logical relationships between configuration
    values and can be called during testing or initialization.
    
    Returns:
        True if configuration is valid
        
    Raises:
        ValueError: If configuration parameters are invalid
    """
    if DECIMAL_PRECISION <= 0:
        raise ValueError(f"DECIMAL_PRECISION must be positive, got {DECIMAL_PRECISION}")
    
    if QUANTITY_DECIMAL_PLACES < 0:
        raise ValueError(f"QUANTITY_DECIMAL_PLACES must be non-negative, got {QUANTITY_DECIMAL_PLACES}")
    
    if QUANTITY_DECIMAL_PLACES > DECIMAL_PRECISION:
        raise ValueError(
            f"QUANTITY_DECIMAL_PLACES ({QUANTITY_DECIMAL_PLACES}) cannot exceed "
            f"DECIMAL_PRECISION ({DECIMAL_PRECISION})"
        )
    
    # Verify quantizer matches decimal places
    expected_quantizer = Decimal("0." + "0" * (QUANTITY_DECIMAL_PLACES - 1) + "1")
    if QUANTITY_QUANTIZER != expected_quantizer and QUANTITY_DECIMAL_PLACES > 0:
        raise ValueError(
            f"QUANTITY_QUANTIZER ({QUANTITY_QUANTIZER}) does not match "
            f"QUANTITY_DECIMAL_PLACES ({QUANTITY_DECIMAL_PLACES})"
        )
    
    return True

# Validate on import
validate_decimal_config()

__all__ = [
    'DECIMAL_PRECISION',
    'QUANTITY_DECIMAL_PLACES',
    'QUANTITY_QUANTIZER',
    'DECIMAL_ROUNDING',
    'quantize_quantity',
    'decimal_from_numeric',
    'to_storage_int',
    'from_storage_int',
    'validate_decimal_config',
]

