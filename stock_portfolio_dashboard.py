import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import io

# Multi-language support
def load_translations():
    translations = {
        "en": {
            "title": "Stock Portfolio Dashboard",
            "upload_file": "Upload CSV File",
            "portfolio_filter": "Portfolio Filter",
            "member_filter": "Member Filter",
            "broker_filter": "Broker Filter",
            "sector_filter": "Sector Filter",
            "summary_table": "Portfolio Summary",
            "detail_table": "Portfolio Details",
            "charts": "Portfolio Analysis Charts",
            "member": "Member",
            "broker": "Broker",
            "company_name": "Company Name",
            "sector": "Sector",
            "investment": "Investment",
            "current_value": "Current Value",
            "hpr": "HPR (%)",
            "quantity": "Quantity",
            "invested_amount": "Invested Amount",
            "holding_period": "Holding Period",
            "portfolio_distribution": "Portfolio Distribution by Sector",
            "member_performance": "Member-wise Performance",
            "broker_comparison": "Broker-wise Comparison",
            "top_performers": "Top Performing Stocks",
            "language": "Language",
            "sort_by": "Sort By",
            "stock_code": "Stock Code",
            "summarize_by": "Summarize By",
            "default_file": "Default File"
        },
        "ta": {
            "title": "பங்கு போர்ட்ஃபோலியோ டாஷ்போர்டு",
            "upload_file": "CSV கோப்பை பதிவேற்றுக",
            "portfolio_filter": "போர்ட்ஃபோலியோ வடிகட்டி",
            "member_filter": "உறுப்பினர் வடிகட்டி",
            "broker_filter": "தரகர் வடிகட்டி",
            "sector_filter": "துறை வடிகட்டி",
            "summary_table": "போர்ட்ஃபோலியோ சுருக்கம்",
            "detail_table": "போர்ட்ஃபோலியோ விவரங்கள்",
            "charts": "போர்ட்ஃபோலியோ பகுப்பாய்வு விளக்கப்படங்கள்",
            "member": "உறுப்பினர்",
            "broker": "தரகர்",
            "company_name": "நிறுவன பெயர்",
            "sector": "துறை",
            "investment": "முதலீடு",
            "current_value": "தற்போதைய மதிப்பு",
            "hpr": "HPR (%)",
            "quantity": "அளவு",
            "invested_amount": "முதலீட்டு தொகை",
            "holding_period": "வைத்திருக்கும் காலம்",
            "portfolio_distribution": "துறை வாரியாக போர்ட்ஃபோலியோ விநியோகம்",
            "member_performance": "உறுப்பினர் வாரியாக செயல்திறன்",
            "broker_comparison": "தரகர் வாரியாக ஒப்பீடு",
            "top_performers": "சிறந்த செயல்திறன் பங்குகள்",
            "language": "மொழி",
            "sort_by": "வரிசைப்படுத்து",
            "stock_code": "பங்கு குறியீடு",
            "summarize_by": "சுருக்கம்",
            "default_file": "இயல்புநிலை கோப்பு"
        }
    }
    return translations

def format_currency(value):
    """Format value as Indian Rupee with proper alignment"""
    if pd.isna(value):
        return "₹0.00"
    return f"₹{value:,.2f}"

def format_percentage(value):
    """Format percentage with 2 decimal places"""
    if pd.isna(value):
        return "0.00%"
    return f"{value:.2f}%"

def calculate_hpr(current_value, cost_value):
    """Calculate Holding Period Return percentage"""
    if cost_value == 0:
        return 0
    return ((current_value - cost_value) / cost_value) * 100

def style_negative_returns(val):
    """Apply conditional formatting for negative returns"""
    if isinstance(val, str) and '%' in val:
        try:
            num_val = float(val.replace('%', ''))
            if num_val < 0:
                return 'background-color: #ffebee; color: #c62828'
            elif num_val > 0:
                return 'background-color: #e8f5e8; color: #2e7d32'
        except:
            pass
    return ''

def create_summary_table(df, translations, lang, group_by='Member'):
    """Create summary table with aggregated data based on grouping option"""
    # Group by the selected option
    if group_by == 'Member':
        summary = df.groupby(['Portfolio', 'Member']).agg({
            'Value At Cost': 'sum',
            'Value At Market Price': 'sum'
        }).reset_index()
        group_col = 'Member'
        group_col_display = translations[lang]['member']
    elif group_by == 'Sector':
        summary = df.groupby(['Portfolio', 'Sector']).agg({
            'Value At Cost': 'sum',
            'Value At Market Price': 'sum'
        }).reset_index()
        group_col = 'Sector'
        group_col_display = translations[lang]['sector']
    elif group_by == 'Broker':
        summary = df.groupby(['Portfolio', 'Broker']).agg({
            'Value At Cost': 'sum',
            'Value At Market Price': 'sum'
        }).reset_index()
        group_col = 'Broker'
        group_col_display = translations[lang]['broker']
    
    # Calculate HPR
    summary['HPR'] = summary.apply(
        lambda row: calculate_hpr(row['Value At Market Price'], row['Value At Cost']), 
        axis=1
    )
    
    # Rename columns for display
    summary_display = summary.copy()
    summary_display = summary_display.rename(columns={
        group_col: group_col_display,
        'Value At Cost': translations[lang]['investment'],
        'Value At Market Price': translations[lang]['current_value'],
        'HPR': translations[lang]['hpr']
    })
    
    # Remove Portfolio column if it's not needed for display
    if 'Portfolio' in summary_display.columns:
        summary_display = summary_display.drop('Portfolio', axis=1)
    
    return summary, summary_display

def create_detail_table(df, translations, lang):
    """Create detailed table with all records"""
    detail = df.copy()
    detail['HPR'] = detail.apply(
        lambda row: calculate_hpr(row['Value At Market Price'], row['Value At Cost']), 
        axis=1
    )
    
    # Rename columns for display
    detail_display = detail.copy()
    detail_display.columns = [
        translations[lang]['member'] if col == 'Member' else
        translations[lang]['broker'] if col == 'Broker' else
        translations[lang]['sector'] if col == 'Sector' else
        translations[lang]['stock_code'] if col == 'Company Name' else
        translations[lang]['quantity'] if col == 'Qty' else
        translations[lang]['invested_amount'] if col == 'Value At Cost' else
        translations[lang]['current_value'] if col == 'Value At Market Price' else
        translations[lang]['hpr'] if col == 'HPR' else col
        for col in detail_display.columns
    ]
    
    return detail, detail_display

def main():
    st.set_page_config(page_title="Stock Portfolio Dashboard", layout="wide")
    
    # Load translations
    translations = load_translations()
    
    # Language selection
    lang = st.sidebar.selectbox(
        "Language / மொழி", 
        options=['en', 'ta'], 
        format_func=lambda x: "English" if x == 'en' else "தமிழ்"
    )
    
    st.title(translations[lang]['title'])
    
    # Sidebar for file upload and filters
    st.sidebar.header("File Upload")
    
    # Option to use default file or upload new file
    use_default = st.sidebar.checkbox(
        f"Use {translations[lang]['default_file']} (portfolio-inputs.csv)",
        value=True
    )
    
    df = None
    
    if use_default:
        # Try to load default file
        try:
            df = pd.read_csv('portfolio-inputs.csv')
            st.sidebar.success("Default file loaded successfully!")
        except FileNotFoundError:
            st.sidebar.error("Default file 'portfolio-inputs.csv' not found. Please upload a file.")
        except Exception as e:
            st.sidebar.error(f"Error loading default file: {str(e)}")
    
    if not use_default or df is None:
        # File upload
        uploaded_file = st.sidebar.file_uploader(
            translations[lang]['upload_file'], 
            type=['csv'],
            help="Upload your portfolio CSV file"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.sidebar.success("File uploaded successfully!")
            except Exception as e:
                st.sidebar.error(f"Error reading file: {str(e)}")
    
    if df is not None:
        try:
            
            # Validate required columns
            required_columns = ['Portfolio', 'Broker', 'Member', 'Company Name', 'Sector', 'Qty', 'Value At Cost', 'Value At Market Price']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing columns: {', '.join(missing_columns)}")
                return
            
            # Clean and prepare data
            df['Value At Cost'] = pd.to_numeric(df['Value At Cost'], errors='coerce').fillna(0)
            df['Value At Market Price'] = pd.to_numeric(df['Value At Market Price'], errors='coerce').fillna(0)
            df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
            
            # Sidebar filters
            st.sidebar.header("Filters")
            
            # Summary grouping option
            summary_options = {
                translations[lang]['member']: 'Member',
                translations[lang]['sector']: 'Sector',
                translations[lang]['broker']: 'Broker'
            }
            selected_summary = st.sidebar.selectbox(
                translations[lang]['summarize_by'],
                list(summary_options.keys()),
                index=0  # Default to Member
            )
            summary_group_by = summary_options[selected_summary]
            
            # Portfolio filter
            portfolios = ['All'] + list(df['Portfolio'].unique())
            selected_portfolio = st.sidebar.selectbox(
                translations[lang]['portfolio_filter'], 
                portfolios
            )
            
            # Member filter
            members = ['All'] + list(df['Member'].unique())
            selected_member = st.sidebar.selectbox(
                translations[lang]['member_filter'], 
                members
            )
            
            # Broker filter
            brokers = ['All'] + list(df['Broker'].unique())
            selected_broker = st.sidebar.selectbox(
                translations[lang]['broker_filter'], 
                brokers
            )
            
            # Sector filter
            sectors = ['All'] + list(df['Sector'].unique())
            selected_sector = st.sidebar.selectbox(
                translations[lang]['sector_filter'], 
                sectors
            )
            
            # Sort options
            sort_options = {
                translations[lang]['member']: 'Member',
                translations[lang]['sector']: 'Sector', 
                translations[lang]['broker']: 'Broker',
                translations[lang]['stock_code']: 'Company Name'
            }
            selected_sort = st.sidebar.selectbox(
                translations[lang]['sort_by'],
                list(sort_options.keys()),
                index=0  # Default to Member
            )
            
            # Apply filters
            filtered_df = df.copy()
            if selected_portfolio != 'All':
                filtered_df = filtered_df[filtered_df['Portfolio'] == selected_portfolio]
            if selected_member != 'All':
                filtered_df = filtered_df[filtered_df['Member'] == selected_member]
            if selected_broker != 'All':
                filtered_df = filtered_df[filtered_df['Broker'] == selected_broker]
            if selected_sector != 'All':
                filtered_df = filtered_df[filtered_df['Sector'] == selected_sector]
            
            if filtered_df.empty:
                st.warning("No data available for the selected filters.")
                return
            
            # Sort data
            sort_column = sort_options[selected_sort]
            filtered_df = filtered_df.sort_values([sort_column, 'Company Name'])
            
            # Create summary and detail tables
            summary_data, summary_display = create_summary_table(filtered_df, translations, lang, summary_group_by)
            detail_data, detail_display = create_detail_table(filtered_df, translations, lang)
            
            # Display Summary Table
            st.header(translations[lang]['summary_table'])
            
            # Format summary table for display
            summary_formatted = summary_display.copy()
            investment_col = translations[lang]['investment']
            current_value_col = translations[lang]['current_value']
            hpr_col = translations[lang]['hpr']
            
            # Apply currency formatting
            summary_formatted[investment_col] = summary_formatted[investment_col].apply(format_currency)
            summary_formatted[current_value_col] = summary_formatted[current_value_col].apply(format_currency)
            summary_formatted[hpr_col] = summary_formatted[hpr_col].apply(format_percentage)
            
            # Apply conditional formatting and display
            styled_summary = summary_formatted.style.applymap(
                style_negative_returns, 
                subset=[hpr_col]
            ).set_properties(**{
                'text-align': 'right'
            }, subset=[investment_col, current_value_col, hpr_col])
            
            st.dataframe(styled_summary, use_container_width=True, hide_index=True)
            
            # Display Detail Table
            st.header(translations[lang]['detail_table'])
            
            # Format detail table for display
            detail_formatted = detail_display.copy()
            invested_amount_col = translations[lang]['invested_amount']
            current_value_col = translations[lang]['current_value']
            hpr_col = translations[lang]['hpr']
            
            # Apply currency formatting
            detail_formatted[invested_amount_col] = detail_formatted[invested_amount_col].apply(format_currency)
            detail_formatted[current_value_col] = detail_formatted[current_value_col].apply(format_currency)
            detail_formatted[hpr_col] = detail_formatted[hpr_col].apply(format_percentage)
            
            # Apply conditional formatting and display
            styled_detail = detail_formatted.style.applymap(
                style_negative_returns, 
                subset=[hpr_col]
            ).set_properties(**{
                'text-align': 'right'
            }, subset=[invested_amount_col, current_value_col, hpr_col])
            
            st.dataframe(styled_detail, use_container_width=True, hide_index=True)
            
            # Charts Section
            st.header(translations[lang]['charts'])
            
            # Create charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Sector-wise distribution pie chart
                sector_summary = filtered_df.groupby('Sector')['Value At Market Price'].sum().reset_index()
                fig_pie = px.pie(
                    sector_summary, 
                    values='Value At Market Price', 
                    names='Sector',
                    title=translations[lang]['portfolio_distribution']
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Member-wise performance bar chart
                member_summary = filtered_df.groupby('Member').agg({
                    'Value At Cost': 'sum',
                    'Value At Market Price': 'sum'
                }).reset_index()
                member_summary['HPR'] = member_summary.apply(
                    lambda row: calculate_hpr(row['Value At Market Price'], row['Value At Cost']), 
                    axis=1
                )
                
                fig_bar = px.bar(
                    member_summary, 
                    x='Member', 
                    y='HPR',
                    title=translations[lang]['member_performance'],
                    color='HPR',
                    color_continuous_scale=['red', 'yellow', 'green']
                )
                fig_bar.update_layout(yaxis_title="HPR (%)")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # Additional charts
            col3, col4 = st.columns(2)
            
            with col3:
                # Broker comparison
                broker_summary = filtered_df.groupby('Broker').agg({
                    'Value At Cost': 'sum',
                    'Value At Market Price': 'sum'
                }).reset_index()
                broker_summary['HPR'] = broker_summary.apply(
                    lambda row: calculate_hpr(row['Value At Market Price'], row['Value At Cost']), 
                    axis=1
                )
                
                fig_broker = px.bar(
                    broker_summary, 
                    x='Broker', 
                    y=['Value At Cost', 'Value At Market Price'],
                    title=translations[lang]['broker_comparison'],
                    barmode='group'
                )
                st.plotly_chart(fig_broker, use_container_width=True)
            
            with col4:
                # Top performing stocks
                stock_performance = filtered_df.copy()
                stock_performance['HPR'] = stock_performance.apply(
                    lambda row: calculate_hpr(row['Value At Market Price'], row['Value At Cost']), 
                    axis=1
                )
                top_stocks = stock_performance.nlargest(10, 'HPR')
                
                fig_top = px.bar(
                    top_stocks, 
                    x='HPR', 
                    y='Company Name',
                    title=translations[lang]['top_performers'],
                    orientation='h',
                    color='HPR',
                    color_continuous_scale=['red', 'yellow', 'green']
                )
                fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_top, use_container_width=True)
            
            # Portfolio Summary Statistics
            st.header("Portfolio Statistics")
            
            total_investment = filtered_df['Value At Cost'].sum()
            total_current_value = filtered_df['Value At Market Price'].sum()
            total_gain_loss = total_current_value - total_investment
            total_hpr = calculate_hpr(total_current_value, total_investment)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label=translations[lang]['investment'],
                    value=format_currency(total_investment)
                )
            
            with col2:
                st.metric(
                    label=translations[lang]['current_value'],
                    value=format_currency(total_current_value)
                )
            
            with col3:
                st.metric(
                    label="Gain/Loss",
                    value=format_currency(total_gain_loss),
                    delta=format_currency(total_gain_loss)
                )
            
            with col4:
                st.metric(
                    label=translations[lang]['hpr'],
                    value=format_percentage(total_hpr),
                    delta=format_percentage(total_hpr)
                )
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    
    else:
        st.info("Please upload a CSV file or ensure 'portfolio-inputs.csv' is in the same directory.")
        
        # Show sample data format
        st.subheader("Expected CSV Format")
        sample_data = pd.DataFrame({
            'Portfolio': ['MBPS'],
            'Broker': ['ICICI Direct'],
            'Member': ['John'],
            'Company Name': ['SAMPLE COMPANY LTD'],
            'Sector': ['Technology'],
            'Qty': [100],
            'Value At Cost': [10000],
            'Value At Market Price': [12000]
        })
        st.dataframe(sample_data, hide_index=True)

if __name__ == "__main__":
    main()