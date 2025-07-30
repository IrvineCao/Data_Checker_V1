import streamlit as st
import pandas as pd
from utils.core.helpers import initialize_session_state
from utils.core.logic import preprocess_uploaded_data, query_database_performance, compare_performance_data
from utils.ui.ui import *

def main():
    
    # Initialize session state and display user message
    initialize_session_state()

    # Setup page
    st.set_page_config(
        page_title="Performance Data Validation",
        page_icon="🔍",
        layout="wide"
    )

# Header
st.title("🔍 Performance Data Validation Tool")

# Main content
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🛍️ Lazada Performance Validation
    
    Select **Lazada** in the sidebar to:
    - Validate Lazada performance files
    - Compare metrics at different levels
    - Get detailed analysis and reports
    
    **Key Features:**
    - Multi-level data support (campaign/object/placement)
    - Automatic data aggregation
    - Visual analytics and insights
    - Detailed validation reports
    """)

with col2:
    st.markdown("""
    ### 🛒 Shopee Performance Validation
    
    Select **Shopee** in the sidebar to:
    - Validate Shopee performance files
    - Compare metrics at different levels
    - Get detailed analysis and reports
    
    **Key Features:**
    - Multi-level data support (campaign/object/placement)
    - Automatic data aggregation
    - Visual analytics and insights
    - Detailed validation reports
    """)

# Additional information
st.divider()
st.subheader("ℹ️ About This Tool")

st.markdown("""
This tool helps you validate performance data from different marketplaces against our database records.
Key features include:

- **🎯 5% Tolerance**: All metrics are validated with a 5% tolerance threshold
- **📊 Multi-Level Support**: Compare data at campaign, object, or placement level
- **📈 Automatic Aggregation**: Option to aggregate all levels for comparison
- **📋 Detailed Reports**: Get comprehensive validation reports and insights
- **📊 Visual Analytics**: Visual representation of validation results
""")


def process_file(uploaded_file):
    """Process uploaded file and display results"""
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
        render_file_info(df_upload)
        
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
        
        # Get comparison mode
        comparison_mode_placeholder = st.empty()
        with comparison_mode_placeholder.container():
            comparison_mode, selected_level = ui.render_comparison_mode(has_level_column, df_upload)
        
        # Process data
        df_processed = preprocess_uploaded_data(df_upload, comparison_mode, selected_level)
        
        # Extract parameters for database query
        unique_storefronts = df_processed['storefront'].unique().tolist()
        unique_months = df_processed['month'].unique().tolist()
        
        st.success(f"✅ Processed {len(df_processed)} rows for comparison")
        
        # Query database
        with st.spinner("🔍 Querying database..."):
            df_database = query_database_performance(
                unique_storefronts, 
                unique_months, 
                comparison_mode, 
                selected_level
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
        
        # Recommendations
        ui.render_recommendations(matches, total_comparisons, comparison_results, missing_file, missing_db)
        
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        with st.expander("🔍 Error Details", expanded=False):
            st.exception(e)

if __name__ == "__main__":
    main()