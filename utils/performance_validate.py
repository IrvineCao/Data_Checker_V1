from utils.helpers import PROJECT_ROOT
from Data.get_data import get_query


# Helper function to build dynamic parameters
def build_validation_params(storefront_ids, months, level_filter=None, aggregate_levels=False):
    """Build parameters for performance validation query."""
    return {
        "storefront_ids": storefront_ids,
        "months": months,
        "level_filter": level_filter,
        "aggregate_levels": aggregate_levels
    }