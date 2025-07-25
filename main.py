import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from utils.helpers import initialize_session_state, display_user_message, trace_function_call
from utils.database import get_connection

from sqlalchemy import text

import io
import plotly.express as px
import plotly.graph_objects as go

initialize_session_state()
display_user_message()

st.set_page_config(
    page_title="Performance Data Validation",
    page_icon="🔍",
    layout="wide"
)

# Load CSS for consistent styling
def load_css():
    st.markdown("""
    <style>
        .validation-result {
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
        }
        .match { background-color: rgba(81, 207, 102, 0.1); border-left: 4px solid #51cf66; }
        .mismatch { background-color: rgba(255, 107, 107, 0.1); border-left: 4px solid #ff6b6b; }
        .missing { background-color: rgba(255, 177, 43, 0.1); border-left: 4px solid #ffb12b; }
        
        .metric-card {
            background: linear-gradient(135deg, rgba(255, 0, 127, 0.05), rgba(0, 255, 204, 0.05));
            border: 1px solid rgba(255, 0, 127, 0.2);
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            text-align: center;
        }
        
        .config-section {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .file-format-example {
            background: rgba(0, 255, 204, 0.05);
            border: 1px solid rgba(0, 255, 204, 0.2);
            border-radius: 8px;
            padding: 1rem;
            font-family: monospace;
            font-size: 0.9rem;
        }
    </style>
    """, unsafe_allow_html=True)

load_css()

# Header
st.title("🔍 Performance Data Validation Tool")
st.markdown("**Validate your performance files against database metrics with intelligent level handling**")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Metrics selection
    st.subheader("📊 Metrics to Validate")
    available_metrics = ["impressions", "clicks", "gmv", "expense", "roas"]
    
    selected_metrics = st.multiselect(
        "Select Metrics",
        available_metrics,
        default=["impressions", "clicks", "gmv", "expense", "roas"],
        help="Choose which metrics to compare between file and database"
    )
    
    # Tolerance settings
    st.subheader("🎯 Tolerance Settings")
    
    # Different tolerances for different metrics
    tolerance_config = {}
    
    col1, col2 = st.columns(2)
    with col1:
        tolerance_config['impressions'] = st.slider("Impressions (%)", 0.0, 20.0, 5.0, 0.1)
        tolerance_config['clicks'] = st.slider("Clicks (%)", 0.0, 20.0, 5.0, 0.1)
        tolerance_config['gmv'] = st.slider("GMV (%)", 0.0, 20.0, 5.0, 0.1)
    
    with col2:
        tolerance_config['expense'] = st.slider("Expense (%)", 0.0, 20.0, 5.0, 0.1)
        tolerance_config['roas'] = st.slider("ROAS (%)", 0.0, 20.0, 10.0, 0.1)
    
    # Comparison mode (will be set after file upload)
    st.subheader("📋 Comparison Mode")
    comparison_mode_placeholder = st.empty()

# Main content
st.divider()

# File Upload Section
col1, col2 = st.columns([1.2, 0.8])

with col1:
    st.subheader("📤 Upload Performance File")
    
    # File format explanation
    st.markdown("""
    <div class='file-format-example'>
    <strong>📋 Expected Format (Multi-Level):</strong><br>
    storefront,month,level,Impression,Clicks,GMV,Expense,ROAS<br>
    55055,1,campaign,485257,15971,242602.46,34572.44,7.02<br>
    55055,1,object,1485257,15971,242602.46,34572.44,7.02<br>
    55056,2,placement,375025,15859,212525.96,34902.75,6.09<br>
    <br>
    <strong>📋 Alternative Format (Aggregated):</strong><br>
    storefront,month,Impression,Clicks,GMV,Expense,ROAS<br>
    55055,1,970514,31942,485204.92,69144.88,7.02<br>
    55056,2,750050,31718,425051.92,69805.50,6.09<br>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose your performance file",
        type=['csv', 'xlsx'],
        help="Upload CSV or Excel file with performance data"
    )

with col2:
    st.subheader("🎯 Validation Query Preview")
    
    with st.expander("📜 SQL Query Structure", expanded=False):
        st.code("""
-- Multi-Level Performance Query
WITH campaign_performance AS (
    SELECT storefront_id, 'campaign' as level, 
           month, impressions, clicks, gmv, expense, roas
    FROM campaigns + performance
),
object_performance AS (
    SELECT storefront_id, 'object' as level,
           month, impressions, clicks, gmv, expense, roas  
    FROM objects + performance
),
placement_performance AS (
    SELECT storefront_id, 'placement' as level,
           month, impressions, clicks, gmv, expense, roas
    FROM placements + performance  
)
SELECT * FROM unified_performance
ORDER BY storefront_id, month, level
        """, language="sql")

# File Processing Section
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
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Rows", len(df_upload))
        with col2:
            unique_storefronts = df_upload['storefront'].nunique() if 'storefront' in df_upload.columns else 0
            st.metric("🏬 Storefronts", unique_storefronts)
        with col3:
            unique_months = df_upload['month'].nunique() if 'month' in df_upload.columns else 0
            st.metric("📅 Months", unique_months)
        
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
        
        # Comparison mode selection (now that we know file structure)
        with comparison_mode_placeholder.container():
            if has_level_column:
                comparison_mode = st.radio(
                    "How to handle levels?",
                    ["keep_separate", "aggregate_all", "filter_level"],
                    format_func=lambda x: {
                        "keep_separate": "📋 Compare each level separately",
                        "aggregate_all": "📈 Sum all levels together", 
                        "filter_level": "🎯 Compare specific level only"
                    }[x],
                    help="Choose how to compare multi-level data with database"
                )
                
                if comparison_mode == "filter_level":
                    available_levels = df_upload['level'].unique()
                    selected_level = st.selectbox("Select Level", available_levels)
                else:
                    selected_level = None
            else:
                comparison_mode = "standard"
                selected_level = None
                st.info("📊 Standard comparison mode (aggregated data)")
        
        # Data preprocessing
        @trace_function_call
        def preprocess_uploaded_data(df, mode, level_filter=None):
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
            
            if mode == "aggregate_all" and 'level' in df.columns:
                # Sum all levels
                df_processed = df.groupby(['storefront', 'month']).agg({
                    'impressions': 'sum',
                    'clicks': 'sum',
                    'gmv': 'sum', 
                    'expense': 'sum',
                    'roas': 'mean'  # Average ROAS
                }).reset_index()
                df_processed['level'] = 'aggregated'
                
            elif mode == "filter_level" and level_filter:
                # Filter to specific level
                df_processed = df[df['level'] == level_filter].copy()
                
            else:
                # Keep as-is (separate levels or already aggregated)
                df_processed = df
            
            return df_processed
        
        df_processed = preprocess_uploaded_data(df_upload, comparison_mode, selected_level)
        
        # Extract parameters for database query
        unique_storefronts = df_processed['storefront'].unique().tolist()
        unique_months = df_processed['month'].unique().tolist()
        
        st.success(f"✅ Processed {len(df_processed)} rows for comparison")
        
        # Database query function
        @st.cache_data(ttl=300)
        @trace_function_call 
        def query_database_performance(storefront_ids, months, mode, level_filter=None):
            """Query database for performance metrics with level handling."""
            
            # Build query parameters based on comparison mode
            if mode == "aggregate_all":
                aggregate_levels = True
                level_filter_param = None
            elif mode == "filter_level":
                aggregate_levels = False
                level_filter_param = level_filter
            else:  # keep_separate or standard
                aggregate_levels = False
                level_filter_param = None
            
            # Multi-level performance query
            query = """
            WITH campaign_performance AS (
                SELECT
                    camp.storefront_id,
                    'campaign' as level,
                    MONTH(perf.created_datetime) as month,
                    SUM(perf.impression) as impressions,
                    SUM(perf.click) as clicks,
                    SUM(perf.ads_gmv) as gmv,
                    SUM(perf.cost) as expense,
                    CASE 
                        WHEN SUM(perf.cost) > 0 THEN SUM(perf.ads_gmv) / SUM(perf.cost)
                        ELSE 0 
                    END as roas
                FROM ads_ops_ads_campaigns camp
                INNER JOIN ads_ops_ads_campaigns_performance perf 
                    ON camp.id = perf.ads_campaign_id
                WHERE camp.storefront_id IN :storefront_ids
                    AND MONTH(perf.created_datetime) IN :months
                    and camp.tool_code NOT in ('LZD_SPONSORED_MAX')
                GROUP BY camp.storefront_id, MONTH(perf.created_datetime)
            ), 
            
            object_performance AS (
                SELECT
                    obj.storefront_id,
                    'object' as level,
                    MONTH(perf.created_datetime) as month,
                    SUM(perf.impression) as impressions,
                    SUM(perf.click) as clicks,
                    SUM(perf.ads_gmv) as gmv,
                    SUM(perf.cost) as expense,
                    CASE 
                        WHEN SUM(perf.cost) > 0 THEN SUM(perf.ads_gmv) / SUM(perf.cost)
                        ELSE 0 
                    END as roas
                FROM ads_ops_ads_objects obj
                INNER JOIN ads_ops_ads_objects_performance perf 
                    ON obj.id = perf.ads_object_id
                WHERE obj.storefront_id IN :storefront_ids
                    AND MONTH(perf.created_datetime) IN :months
                    and obj.tool_code NOT in ('LZD_SPONSORED_MAX')
                GROUP BY obj.storefront_id, MONTH(perf.created_datetime)
            ),
            
            placement_performance AS (
                SELECT
                    pl.storefront_id,
                    'placement' as level,
                    MONTH(perf.created_datetime) as month,
                    SUM(perf.impression) as impressions,
                    SUM(perf.click) as clicks,
                    SUM(perf.ads_gmv) as gmv,
                    SUM(perf.cost) as expense,
                    CASE 
                        WHEN SUM(perf.cost) > 0 THEN SUM(perf.ads_gmv) / SUM(perf.cost)
                        ELSE 0 
                    END as roas
                FROM ads_ops_ads_placements pl
                INNER JOIN ads_ops_ads_placements_performance perf 
                    ON pl.id = perf.ads_placement_id
                WHERE pl.storefront_id IN :storefront_ids
                    AND MONTH(perf.created_datetime) IN :months
                    AND perf.timing = 'daily'
                    and pl.tool_code NOT in ('LZD_SPONSORED_MAX')
                GROUP BY pl.storefront_id, MONTH(perf.created_datetime)
            ),
            
            unified_performance AS (
                SELECT * FROM campaign_performance
                UNION ALL
                SELECT * FROM object_performance
                UNION ALL
                SELECT * FROM placement_performance
            )
            
            SELECT 
                storefront_id,
                CASE 
                    WHEN :aggregate_levels = true THEN 'aggregated'
                    ELSE level 
                END as level,
                month,
                CASE 
                    WHEN :aggregate_levels = true THEN SUM(impressions)
                    ELSE impressions 
                END as impressions,
                CASE 
                    WHEN :aggregate_levels = true THEN SUM(clicks)
                    ELSE clicks 
                END as clicks,
                CASE 
                    WHEN :aggregate_levels = true THEN SUM(gmv)
                    ELSE gmv 
                END as gmv,
                CASE 
                    WHEN :aggregate_levels = true THEN SUM(expense)
                    ELSE expense 
                END as expense,
                CASE 
                    WHEN :aggregate_levels = true AND SUM(expense) > 0 THEN SUM(gmv) / SUM(expense)
                    WHEN :aggregate_levels = false THEN roas
                    ELSE 0 
                END as roas
            FROM unified_performance
            GROUP BY 
                storefront_id,
                month,
                CASE 
                    WHEN :aggregate_levels = true THEN 'aggregated'
                    ELSE level 
                END
            ORDER BY storefront_id, month, level
            """
            
            params = {
                "storefront_ids": tuple(storefront_ids),
                "months": tuple(months),
                "level_filter": level_filter_param,
                "aggregate_levels": aggregate_levels
            }
            
            with get_connection() as db:
                return pd.read_sql(text(query), db.connection(), params=params)
        
        # Execute database query
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
        
        # Comparison logic
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
        total_comparisons = len(comparison_results)
        matches = len(comparison_results[comparison_results['status'] == 'match'])
        mismatches = len(comparison_results[comparison_results['status'] == 'mismatch'])
        missing_file = len(comparison_results[comparison_results['status'] == 'missing_in_file'])
        missing_db = len(comparison_results[comparison_results['status'] == 'missing_in_db'])
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <h3 style='color: #51cf66; margin: 0;'>✅ Matches</h3>
                <h2 style='margin: 0.5rem 0;'>{matches}</h2>
                <p style='margin: 0; color: #a1a1aa;'>{(matches/total_comparisons)*100:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='metric-card'>
                <h3 style='color: #ff6b6b; margin: 0;'>❌ Mismatches</h3>
                <h2 style='margin: 0.5rem 0;'>{mismatches}</h2>
                <p style='margin: 0; color: #a1a1aa;'>{(mismatches/total_comparisons)*100:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class='metric-card'>
                <h3 style='color: #ffb12b; margin: 0;'>📁 Missing (File)</h3>
                <h2 style='margin: 0.5rem 0;'>{missing_file}</h2>
                <p style='margin: 0; color: #a1a1aa;'>{(missing_file/total_comparisons)*100:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class='metric-card'>
                <h3 style='color: #ffb12b; margin: 0;'>🗄️ Missing (DB)</h3>
                <h2 style='margin: 0.5rem 0;'>{missing_db}</h2>
                <p style='margin: 0; color: #a1a1aa;'>{(missing_db/total_comparisons)*100:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class='metric-card'>
                <h3 style='color: #ffffff; margin: 0;'>📊 Total</h3>
                <h2 style='margin: 0.5rem 0;'>{total_comparisons}</h2>
                <p style='margin: 0; color: #a1a1aa;'>Comparisons</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Visual Analysis
        if not comparison_results.empty:
            st.subheader("📈 Visual Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Status distribution pie chart
                status_counts = comparison_results['status'].value_counts()
                fig_pie = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Validation Status Distribution",
                    color_discrete_map={
                        'match': '#51cf66',
                        'mismatch': '#ff6b6b', 
                        'missing_in_file': '#ffb12b',
                        'missing_in_db': '#ffd43b'
                    }
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Accuracy by metric
                metric_accuracy = comparison_results.groupby('metric')['status'].apply(
                    lambda x: (x == 'match').sum() / len(x) * 100
                ).reset_index()
                metric_accuracy.columns = ['metric', 'accuracy']
                
                fig_bar = px.bar(
                    metric_accuracy,
                    x='metric',
                    y='accuracy',
                    title="Accuracy by Metric",
                    color='accuracy',
                    color_continuous_scale='RdYlGn'
                )
                fig_bar.update_layout(yaxis_title="Accuracy (%)")
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Detailed results tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 All Results", 
            "❌ Mismatches Only", 
            "📊 Summary by Storefront",
            "📈 Trend Analysis"
        ])
        
        with tab1:
            # Color-coded results
            def highlight_status(val):
                if val == 'match':
                    return 'background-color: rgba(81, 207, 102, 0.2)'
                elif val == 'mismatch':
                    return 'background-color: rgba(255, 107, 107, 0.2)'
                elif 'missing' in str(val):
                    return 'background-color: rgba(255, 177, 43, 0.2)'
                return ''
            
            styled_results = comparison_results.style.applymap(
                highlight_status, subset=['status']
            ).format({
                'file_value': '{:.2f}',
                'db_value': '{:.2f}', 
                'difference_pct': '{:.2f}%'
            })
            
            st.dataframe(styled_results, use_container_width=True)
        
        with tab2:
            mismatches_only = comparison_results[comparison_results['status'] == 'mismatch']
            if not mismatches_only.empty:
                st.dataframe(
                    mismatches_only.style.format({
                        'file_value': '{:.2f}',
                        'db_value': '{:.2f}',
                        'difference_pct': '{:.2f}%'
                    }),
                    use_container_width=True
                )
                
                # Worst mismatches
                st.subheader("🔥 Largest Discrepancies")
                worst_mismatches = mismatches_only.nlargest(10, 'difference_pct')
                st.dataframe(worst_mismatches[['storefront_id', 'month', 'level', 'metric', 'file_value', 'db_value', 'difference_pct']], use_container_width=True)
            else:
                st.success("🎉 No mismatches found! All data matches within tolerance.")
        
        with tab3:
            # Summary by storefront
            storefront_summary = comparison_results.groupby(['storefront_id', 'status']).size().unstack(fill_value=0)
            storefront_summary['total'] = storefront_summary.sum(axis=1)
            storefront_summary['accuracy'] = (storefront_summary.get('match', 0) / storefront_summary['total'] * 100).round(2)
            
            st.dataframe(storefront_summary.style.format({'accuracy': '{:.2f}%'}), use_container_width=True)
        
        with tab4:
            if 'month' in comparison_results.columns:
                # Trend analysis by month
                monthly_accuracy = comparison_results.groupby(['month', 'metric'])['status'].apply(
                    lambda x: (x == 'match').sum() / len(x) * 100
                ).reset_index()
                monthly_accuracy.columns = ['month', 'metric', 'accuracy']
                
                fig_trend = px.line(
                    monthly_accuracy,
                    x='month',
                    y='accuracy',
                    color='metric',
                    title="Accuracy Trend by Month",
                    markers=True
                )
                fig_trend.update_layout(yaxis_title="Accuracy (%)")
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("📊 Trend analysis requires monthly data")
        
        # Export Results
        st.divider()
        st.subheader("📥 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Detailed results CSV
            csv_detailed = comparison_results.to_csv(index=False)
            st.download_button(
                label="📊 Download Detailed Results",
                data=csv_detailed,
                file_name=f"validation_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Summary report CSV
            summary_data = {
                'Metric': ['Total Comparisons', 'Matches', 'Mismatches', 'Missing in File', 'Missing in DB', 'Overall Accuracy'],
                'Value': [total_comparisons, matches, mismatches, missing_file, missing_db, f"{(matches/total_comparisons)*100:.2f}%"]
            }
            summary_df = pd.DataFrame(summary_data)
            csv_summary = summary_df.to_csv(index=False)
            
            st.download_button(
                label="📋 Download Summary Report",
                data=csv_summary,
                file_name=f"validation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Recommendations section
        st.divider()
        st.subheader("💡 Recommendations")
        
        if matches / total_comparisons >= 0.95:
            st.success("🎉 **Excellent!** Your data has >95% accuracy. Minor discrepancies are within acceptable ranges.")
        elif matches / total_comparisons >= 0.85:
            st.warning("⚠️ **Good but needs attention.** 85-95% accuracy detected. Review mismatches for potential data issues.")
        else:
            st.error("🚨 **Action required!** <85% accuracy detected. Significant data discrepancies need investigation.")
        
        # Specific recommendations based on results
        if mismatches > 0:
            worst_metric = comparison_results[comparison_results['status'] == 'mismatch']['metric'].value_counts().index[0]
            st.info(f"🎯 **Focus Area:** {worst_metric.title()} has the most mismatches. Consider reviewing data collection for this metric.")
        
        if missing_file > 0 or missing_db > 0:
            st.info("📊 **Data Gaps:** Some data points are missing in file or database. Check data completeness for affected periods.")
        
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        with st.expander("🔍 Error Details", expanded=False):
            st.exception(e)

else:
    # Help section when no file uploaded
    st.info("👆 **Please upload a file to begin validation**")
    
    st.subheader("📚 How to Use This Tool")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 **Step-by-Step Guide:**
        
        1. **📤 Upload your file** (CSV or Excel format)
        2. **⚙️ Configure settings** in the sidebar
        3. **🔍 Review file detection** and choose comparison mode
        4. **📊 Analyze results** in the validation dashboard
        5. **📥 Download reports** for further analysis
        
        ### 📋 **File Format Requirements:**
        
        **Multi-Level Format:**
        - `storefront`: Storefront ID (numeric)
        - `month`: Month number (1-12) 
        - `level`: campaign/object/placement
        - `Impression`, `Clicks`, `GMV`, `Expense`, `ROAS`: Metric values
        
        **Aggregated Format:**
        - `storefront`: Storefront ID (numeric)
        - `month`: Month number (1-12)
        - `Impression`, `Clicks`, `GMV`, `Expense`, `ROAS`: Metric values
        """)
    
    with col2:
        st.markdown("""
        ### 🎛️ **Comparison Modes:**
        
        **📋 Keep Separate:** Compare each level (campaign/object/placement) individually
        
        **📈 Aggregate All:** Sum all levels together for comparison
        
        **🎯 Filter Level:** Compare only specific level (e.g., only campaigns)
        
        ### 🎯 **Tolerance Settings:**
        
        Set different tolerance levels for each metric:
        - **Volume metrics** (Impressions, Clicks): Usually 5-10%
        - **Revenue metrics** (GMV, Expense): Usually 5-15% 
        - **Ratio metrics** (ROAS): Usually 10-20%
        
        ### 📊 **Understanding Results:**
        
        - **✅ Match**: Within tolerance range
        - **❌ Mismatch**: Exceeds tolerance threshold
        - **⚠️ Missing**: Data exists in one source only
        """)

# Advanced Features Section
st.divider()
st.subheader("🚀 Advanced Features")

with st.expander("🔧 Advanced Configuration", expanded=False):
    st.markdown("""
    ### 🎛️ **Custom Tolerance by Storefront**
    
    Different storefronts may have different data quality standards. You can set custom tolerances:
    
    - **High-volume storefronts**: Lower tolerance (2-5%)
    - **New storefronts**: Higher tolerance (10-15%)
    - **Test storefronts**: Very high tolerance (20%+)
    """)
    
    # Advanced tolerance settings
    if st.checkbox("Enable Storefront-Specific Tolerances"):
        st.info("🔧 Feature coming soon! Currently uses global tolerances.")

with st.expander("📊 Data Quality Insights", expanded=False):
    st.markdown("""
    ### 🎯 **Common Data Quality Issues:**
    
    **High ROAS Mismatches:**
    - Usually caused by timing differences in GMV vs Cost recording
    - Check if GMV and Cost are from same time period
    
    **Volume Mismatches (Impressions/Clicks):**
    - May indicate different counting methodologies
    - Verify if both sources count unique vs total events consistently
    
    **Missing Data Patterns:**
    - File missing recent data: Export timing issue
    - Database missing data: Pipeline delays or failures
    
    ### 🔍 **Investigation Tips:**
    
    1. **Start with largest discrepancies** (highest %)
    2. **Group by time period** to identify systematic issues
    3. **Compare similar storefronts** to identify outliers
    4. **Check data collection timestamps** for timing mismatches
    """)

with st.expander("🤖 Automation & Scheduling", expanded=False):
    st.markdown("""
    ### ⚡ **Future Enhancements:**
    
    - **🕐 Scheduled Validation**: Automatic daily/weekly validation runs
    - **📧 Email Alerts**: Notifications when accuracy drops below threshold
    - **📊 Historical Tracking**: Track data quality trends over time
    - **🔗 API Integration**: Programmatic access for automated workflows
    - **📱 Mobile Dashboard**: View validation results on mobile devices
    
    *These features are in development. Stay tuned!*
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #a1a1aa; padding: 1rem;'>
    <p>🔍 <strong>Performance Data Validation Tool</strong> | Built for data accuracy and peace of mind</p>
    <p><em>"Trust, but verify. Especially when it comes to performance data."</em></p>
</div>
""", unsafe_allow_html=True)