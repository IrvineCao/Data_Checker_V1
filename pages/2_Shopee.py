import streamlit as st
import pandas as pd
from utils.helpers import initialize_session_state
from utils.logic import preprocess_uploaded_data, query_database_performance, compare_performance_data
from utils import ui
from utils.ui import *


def main():
    load_css()
    # Initialize session state and display user message
    initialize_session_state()

    # Setup page
    st.set_page_config(
        page_title="Shopee Performance Data Validation",
        page_icon="🛒",
        layout="wide"
    )
    st.title("🛒 Shopee Performance Data Validation")
    st.markdown("**Validate your Shopee performance files against database metrics**")

    # Get configuration from sidebar
    selected_metrics, tolerance_config = ui.render_sidebar()

    # File upload section
    uploaded_file = ui.render_file_upload_section(marketplace="Shopee")
    
    # Process uploaded file
    if uploaded_file is not None:
        st.divider()
        
        try:
            # Read uploaded file
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! Found {len(df_upload)} rows")
            
            # Detect file structure
            has_level_column = 'level' in df_upload.columns.str.lower()
            
            # Display file info
            ui.render_file_info(df_upload)
            
            # File preview
            with st.expander("👀 File Preview (First 10 rows)", expanded=False):
                st.dataframe(df_upload.head(10), use_container_width=True)
            
            # Validate required columns
            if has_level_column:
                required_columns = ['storefront', 'month', 'level']
                file_type = "Multi-Level"
                st.info("🔍 **Detected:** Multi-level file with campaign/object/placement data")
            else:
                required_columns = ['storefront', 'month'] 
                file_type = "Aggregated"
                st.info("📊 **Detected:** Aggregated file with combined metrics")
            
            # Check for required columns
            missing_columns = [col for col in required_columns if col not in df_upload.columns]
            if missing_columns:
                st.error(f"❌ Missing required columns: {missing_columns}")
                st.stop()
            
            # Process data
            df_processed = preprocess_uploaded_data(df_upload)
            
            # Extract parameters for database query
            unique_storefronts = df_processed['storefront'].unique().tolist()
            unique_months = df_processed['month'].unique().tolist()
            
            st.success(f"✅ Processed {len(df_processed)} rows for comparison")
            
            # Query database
            with st.spinner("🔍 Querying database..."):
                df_database = query_database_performance(
                    unique_storefronts, 
                    unique_months, 
                    marketplace="shopee"  # Add marketplace parameter
                )
            
            if df_database.empty:
                st.warning("⚠️ No data found in database for the specified criteria")
                st.stop()
            
            st.success(f"✅ Database query completed! Found {len(df_database)} records")
            
            # Show database preview
            with st.expander("🗄️ Database Results Preview", expanded=False):
                st.dataframe(df_database.head(10), use_container_width=True)
            
            # Perform comparison
            with st.spinner("🔄 Comparing data..."):
                comparison_results = compare_performance_data(
                    df_processed.copy(), 
                    df_database.copy(), 
                    selected_metrics, 
                    tolerance_config
                )
            
            # Display Results
            st.divider()
            st.subheader("📊 Validation Results")
            
            # Summary metrics
            total_comparisons, matches, mismatches, missing_file, missing_db = ui.render_results_summary(comparison_results)
            
            # Visual Analysis
            if not comparison_results.empty:
                ui.render_visual_analysis(comparison_results)
            
            # Detailed results
            ui.render_detailed_results(comparison_results)
            
            # Export section
            ui.render_export_section(comparison_results, total_comparisons, matches, mismatches, missing_file, missing_db)
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            with st.expander("🔍 Error Details", expanded=False):
                st.exception(e)

if __name__ == "__main__":
    main() 