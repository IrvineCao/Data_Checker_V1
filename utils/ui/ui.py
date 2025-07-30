import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def load_css():
    """Load custom CSS from file"""
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_file_upload_section(marketplace=""):
    """Render file upload section"""
    col1, col2 = st.columns([1.2, 0.8])
    
    with col1:
        st.subheader("📤 Upload Performance File")
        
        # File format explanation
        st.markdown(f"""
        <div class='file-format-example'>
        <strong>📋 Expected Format (Multi-Level):</strong><br>
        storefront,month,level,Impression,Clicks,GMV,Expense,ROAS<br>
        55055,1,campaign,485257,15971,242602.46,34572.44,7.02<br>
        55055,1,object,1485257,15971,242602.46,34572.44,7.02<br>
        55056,2,placement,375025,15859,212525.96,34902.75,6.09<br>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""---""")

        uploaded_file = st.file_uploader(
            f"Choose your {marketplace} performance file" if marketplace else "Choose your performance file",
            type=['csv', 'xlsx'],
            help=f"Upload CSV or Excel file with {marketplace} performance data" if marketplace else "Upload CSV or Excel file with performance data"
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
            
    return uploaded_file

def render_file_info(df):
    """Render file information"""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Rows", len(df))
    with col2:
        unique_storefronts = df['storefront'].nunique() if 'storefront' in df.columns else 0
        st.metric("🏬 Storefronts", unique_storefronts)
    with col3:
        unique_months = df['month'].nunique() if 'month' in df.columns else 0
        st.metric("📅 Months", unique_months)

def render_results_summary(comparison_results):
    """Render summary metrics"""
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
    
    return total_comparisons, matches, mismatches, missing_file, missing_db

def render_visual_analysis(comparison_results):
    """Render visual analysis section"""
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

def render_detailed_results(comparison_results):
    """Render detailed results tabs"""
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
        
        styled_results = comparison_results.style.map(
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

def render_export_section(comparison_results, total_comparisons, matches, mismatches, missing_file, missing_db):
    """Render export section"""
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