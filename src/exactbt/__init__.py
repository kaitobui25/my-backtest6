"""
ExactBT package.

This project uses one authoritative execution loop for both broad parameter
search and detailed trade recording. Strategy modules only provide their own
state transition function; they never reimplement entry, exit, fees, slippage,
SL/TP ordering, or performance metrics.
"""

from .constants import ENGINE_VERSION

__all__ = ["ENGINE_VERSION"]
