# data_logic/performance_validation_data.py

from utils.config import PROJECT_ROOT
import streamlit as st
from Data.get_data import get_query



# Helper function to build dynamic parameters
def build_validation_params(storefront_ids, months, level_filter=None, aggregate_levels=False):
    """
    Build parameters for performance validation query.
    
    Args:
        storefront_ids: List of storefront IDs
        months: List of month numbers (1-12)
        level_filter: 'campaign', 'object', 'placement', or None for all
        aggregate_levels: True to sum all levels, False to keep separate
    
    Returns:
        Dictionary of query parameters
    """
    return {
        "storefront_ids": storefront_ids,
        "months": months,
        "level_filter": level_filter,
        "aggregate_levels": aggregate_levels
    }