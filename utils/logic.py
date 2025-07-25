import pandas as pd
import numpy as np
from sqlalchemy import text
from utils.database import get_connection
from utils.helpers import trace_function_call
from Data.get_data import get_query
import streamlit as st

@trace_function_call
def preprocess_uploaded_data(df, level_filter=None):
    """Clean and prepare uploaded data for comparison."""
    df = df.copy()
    
    # Standardize column names
    df.columns = df.columns.str.lower()
    column_mapping = {
        'impression': 'impressions',
        'expense': 'expense',
        'clicks': 'clicks',
        'gmv': 'gmv', 
        'roas': 'roas'
    }
    df = df.rename(columns=column_mapping)
    
    # Ensure storefront is integer
    df['storefront'] = df['storefront'].astype(int)
    
    return df

@trace_function_call 
def query_database_performance(storefront_ids, months, level_filter=None, marketplace=None):
    """Query database for performance metrics with level handling."""
    
    # Build query parameters based on comparison mode
    aggregate_levels = False
    level_filter_param = None
    
    # Determine marketplace from current page if not provided
    if marketplace is None:
        marketplace = st.session_state.get('current_page', 'Home').lower()
    
    # Get query based on marketplace
    if marketplace == 'lazada':
        query = get_query("data_lazada")
    elif marketplace == 'shopee':
        query = get_query("data_shopee")
    else:
        raise ValueError("Invalid marketplace. Must be 'lazada' or 'shopee'")
    
    # Convert lists to tuples for IN clause
    storefront_tuple = tuple(storefront_ids)
    months_tuple = tuple(months)
    
    params = {
        "storefront_ids": storefront_tuple,
        "months": months_tuple,
        "level_filter": level_filter_param,
        "aggregate_levels": aggregate_levels
    }
    
    with get_connection() as db:
        return pd.read_sql(text(query), db.connection(), params=params)

@trace_function_call
def compare_performance_data(df_file, df_db, metrics, tolerances):
    """Compare performance metrics between file and database."""
    results = []
    
    # Prepare merge keys
    if 'level' in df_file.columns and 'level' in df_db.columns:
        merge_keys = ['storefront', 'month', 'level']
        df_file.rename(columns={'storefront': 'storefront_id'}, inplace=True)
    else:
        merge_keys = ['storefront', 'month']
        df_file.rename(columns={'storefront': 'storefront_id'}, inplace=True)
    
    # Merge dataframes  
    df_merged = pd.merge(
        df_file, df_db,
        left_on=[col.replace('storefront', 'storefront_id') for col in merge_keys],
        right_on=[col.replace('storefront', 'storefront_id') for col in merge_keys],
        how='outer',
        suffixes=('_file', '_db')
    )
    
    for _, row in df_merged.iterrows():
        storefront_id = row['storefront_id']
        month = row['month']
        level = row.get('level', 'N/A')
        
        for metric in metrics:
            file_col = f"{metric}_file"
            db_col = f"{metric}_db"
            
            file_value = row.get(file_col, np.nan)
            db_value = row.get(db_col, np.nan)
            
            # Get tolerance for this metric
            tolerance = tolerances.get(metric, 5.0)
            
            # Determine comparison result
            if pd.isna(file_value) and pd.isna(db_value):
                status = "both_missing"
                diff_pct = 0
            elif pd.isna(file_value):
                status = "missing_in_file"
                diff_pct = np.inf
            elif pd.isna(db_value):
                status = "missing_in_db"
                diff_pct = np.inf
            else:
                # Calculate percentage difference
                if db_value != 0:
                    diff_pct = abs((file_value - db_value) / db_value) * 100
                else:
                    diff_pct = 0 if file_value == 0 else float('inf')
                
                if diff_pct <= tolerance:
                    status = "match"
                else:
                    status = "mismatch"
            
            results.append({
                'storefront_id': storefront_id,
                'month': month,
                'level': level,
                'metric': metric,
                'file_value': file_value,
                'db_value': db_value,
                'difference_pct': diff_pct,
                'tolerance': tolerance,
                'status': status
            })
    
    return pd.DataFrame(results)