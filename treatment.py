import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

API_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQxN8g_GH_fD3AqSLH-17joABrioyI5Cq3iAsNozNKGPyyhF_1U4H2xA6LPw5X9OJYsdKcBvE1swuHZ/pub?output=csv"
st.set_page_config(layout="wide")

def fetch_data():
    try:
        # Read the Google Sheets CSV directly into a DataFrame
        df = pd.read_csv(API_URL)
        return df
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()


st.title("My Daily Study Routine")

if st.button("Refresh Data"):
    data = fetch_data()
    df = pd.DataFrame(data)
else:
    data = fetch_data()
    df = pd.DataFrame(data)

if not df.empty:
    df['Hours'] = pd.to_numeric(df['Hours'], errors='coerce')
    df['Full_Date'] = pd.to_datetime(df['Full_Date'])

    df_daily = df.groupby("Full_Date")['Hours'].sum().reset_index()
    df_daily['Rolling Volatility'] = df_daily['Hours'].rolling(window=7).std()
    df_daily['Week'] = df_daily['Full_Date'].dt.to_period('W').apply(lambda r: r.start_time)
    df_weekly = df_daily.groupby('Week')['Hours'].mean().reset_index()
    df_weekly['Hours'] = df_weekly['Hours'].round(2)

    # Donut chart for today's study hours by subject
    today = datetime.now() - timedelta(hours=3)
    today = today.date()
    df_today = df[df['Full_Date'].dt.date == today]

    if not df_today.empty:
        fig_today = px.pie(df_today, values='Hours', names='Study', title='Today\'s Study Hours by Subject',
                           hole=0.4, color='Hours')
        fig_today.update_traces(textinfo='label+value')  # Show label and actual hours
        fig_today.update_layout(title_font=dict(size=24),
                                width=600, height=400)
        
        # Create columns for the donut chart and the total hours card
        col1, col2 = st.columns(2)

        with col1:
            st.plotly_chart(fig_today)

        with col2:
            total_hours_today = df_today['Hours'].sum()
            st.markdown(f"<h3 style='text-align: center; font-size: 18px;'>Total Hours Studied Today</h3>", unsafe_allow_html=True)
            st.markdown(f"<h1 style='text-align: center; font-size: 75px; color: orange; margin-top: 60px'>{total_hours_today:.2f} Hours</h1>", unsafe_allow_html=True)

    if not df_daily.empty:
        plot_option = st.selectbox("Select Plot Type:", ("Total Hours", "Rolling Volatility", "Weekly Average"))

        if plot_option == "Total Hours":
            fig = px.line(df_daily, x='Full_Date', y='Hours', 
                          title='Total Hours Per Day',
                          labels={'Full_Date': 'Date', 'Hours': 'Total Hours'},
                          markers=True)
            fig.update_traces(line=dict(width=4, color='orange'),
                              marker=dict(size=8, symbol='circle'))
            fig.update_layout(title_font=dict(size=24),
                              xaxis_title_font=dict(size=18),
                              yaxis_title_font=dict(size=18),
                              legend=dict(title_font=dict(size=16), font=dict(size=14)),
                              width=1800, height=460)
            st.plotly_chart(fig)

        elif plot_option == "Rolling Volatility":
            fig_volatility = px.line(df_daily, x='Full_Date', y='Rolling Volatility',
                                     title='7-Day Rolling Volatility',
                                     labels={'Full_Date': 'Date', 'Rolling Volatility': 'Volatility'},
                                     markers=True)
            fig_volatility.update_traces(line=dict(width=4, color='royalblue'),
                                         marker=dict(size=8, symbol='circle'))
            fig_volatility.update_layout(title_font=dict(size=24),
                                          xaxis_title_font=dict(size=18),
                                          yaxis_title_font=dict(size=18),
                                          legend=dict(title_font=dict(size=16), font=dict(size=14)),
                                          width=1800, height=600)
            st.plotly_chart(fig_volatility)

        elif plot_option == "Weekly Average":
            fig_weekly = px.bar(df_weekly, x='Week', y='Hours',
                                 title='Weekly Average Study Hours',
                                 labels={'Week': 'Week Start Date', 'Hours': 'Average Hours'},
                                 text=df_weekly['Hours'].apply(lambda x: f"{x:.2f}"),
                                 color='Hours',
                                 color_continuous_scale=px.colors.sequential.Viridis)
            fig_weekly.update_traces(marker=dict(line=dict(width=1, color='black')))
            fig_weekly.update_layout(title_font=dict(size=24),
                                      xaxis_title_font=dict(size=18),
                                      yaxis_title_font=dict(size=18),
                                      legend=dict(title_font=dict(size=16), font=dict(size=14)),
                                      width=1800, height=600)
            st.plotly_chart(fig_weekly)

    st.subheader("Total Hours by Subject")
    df_study = df.groupby("Study")['Hours'].sum().reset_index()
    df_study = df_study.sort_values(by='Hours', ascending=False)

    if not df_study.empty:
        fig_study = px.bar(df_study, x='Study', y='Hours', 
                           title='Total Hours by Study',
                           labels={'Study': 'Study', 'Hours': 'Total Hours'},
                           text='Hours',
                           color='Hours',
                           color_continuous_scale=px.colors.sequential.Viridis)
        fig_study.update_layout(width=1800)
        st.plotly_chart(fig_study)

    last_15_days = datetime.now() - timedelta(days=15)
    df_recent = df[df['Full_Date'] >= last_15_days]
    df_study_recent = df_recent.groupby("Study")['Hours'].sum().reset_index()
    top_studies = df_study_recent.sort_values(by='Hours', ascending=False).head(3)

    st.subheader("Top 3 Subjects Studied in the Last 15 Days")
    for index, row in top_studies.iterrows():
        st.metric(label=row['Study'], value=f"{row['Hours']:.2f} Hours")

    total_hours = df['Hours'].sum()
    days_equivalent = total_hours / 24
    max_hours_day = df_daily.loc[df_daily['Hours'].idxmax()]
    record_hours = max_hours_day['Hours']
    record_date = max_hours_day['Full_Date'].strftime("%Y-%m-%d")

    st.markdown("<h3 style='color: lightblue; font-family: Arial; margin-top: 40px'>- Total Hours Studied -</h3>", unsafe_allow_html=True)

    df_daily = df_daily.sort_values(by='Full_Date')
    df_daily['Studied'] = df_daily['Hours'] > 0
    df_daily['Day_Diff'] = df_daily['Full_Date'].diff().dt.days.fillna(1)
    df_daily['Is_Consecutive'] = (df_daily['Day_Diff'] == 1) & df_daily['Studied']
    df_daily['Streak_Group'] = (~df_daily['Is_Consecutive']).cumsum()
    df_streaks = df_daily[df_daily['Studied']].groupby('Streak_Group').size().reset_index(name='Streak_Length')
    max_streak = df_streaks['Streak_Length'].max()

    last_zero_day = df_daily[df_daily['Hours'] == 0]['Full_Date'].max()
    current_streak = (datetime.now().date() - last_zero_day.date()).days if not pd.isnull(last_zero_day) else 0

    distinct_study_days = df_daily['Full_Date'][df_daily['Studied']].nunique()
    days_without_study = df_daily[~df_daily['Studied']]['Full_Date'].nunique()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Total Hours", value=f"{total_hours:.2f} Hours")
        st.metric(label="Longest Study Streak", value=f"{max_streak} Days")

    with col2:
        st.metric(label="Total time (in days)", value=f"{days_equivalent:.2f} Days")
        st.metric(label="Current Study Streak", value=f"{current_streak} Days")

    with col3:
        st.metric(label="Record Day", value=f"{record_hours:.2f} Hours", delta=f"On {record_date}")
        st.metric(label="Distinct Days Studied", value=f"{distinct_study_days} Days")

    with col4:
        st.metric(label="Started on", value="2024-05-12")
        st.metric(label="No study days", value=f"{days_without_study} Days")


    ######################################
    
        # Add a central title
    st.markdown(f"<h3 style='text-align: center; font-size: 45px; margin-top: 60px;'>Insights</h3>", unsafe_allow_html=True)

    # Input for custom "Last X Days" and date filter
    last_x_days = st.slider("Select the number of days for the recent period:", min_value=1, max_value=365, value=30)
    last_x_days_date = datetime.now() - timedelta(days=last_x_days)
    st.markdown(f"<h3 style='font-size: 12px;'>Disclaimer: The Time of the Day started being recorded on 2024-10-05</h3>", unsafe_allow_html=True)

    # Switch for entire period or custom range
    date_filter = st.radio("Select Time Period", (f"Last {last_x_days} Days", "Entire Period"))

    if date_filter == f"Last {last_x_days} Days":
        df_filtered = df[df['Full_Date'] >= last_x_days_date]
    else:
        df_filtered = df

    # Add a new column for the day of the week
    df_filtered['Day_of_Week'] = df_filtered['Full_Date'].dt.day_name()

    # Calculate total hours for each day of the week
    total_hours_per_weekday = df_filtered.groupby('Day_of_Week')['Hours'].sum().reset_index()

    # Calculate the number of unique study days for each day of the week
    unique_days_per_weekday = df_filtered.groupby('Day_of_Week')['Full_Date'].nunique().reset_index()

    # Merge the two DataFrames
    average_hours_per_weekday = pd.merge(total_hours_per_weekday, unique_days_per_weekday, on='Day_of_Week')
    average_hours_per_weekday['Average_Hours'] = average_hours_per_weekday['Hours'] / average_hours_per_weekday['Full_Date']

    # Reorder the days of the week
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    average_hours_per_weekday['Day_of_Week'] = pd.Categorical(average_hours_per_weekday['Day_of_Week'], categories=days_order, ordered=True)
    average_hours_per_weekday = average_hours_per_weekday.sort_values('Day_of_Week')

    # Plot the average study hours by day of the week
    average_hours_per_weekday['Average_Hours'] = average_hours_per_weekday['Average_Hours'].round(2)  # Round to 2 decimals

    fig_avg_weekday = px.bar(
        average_hours_per_weekday, 
        x='Day_of_Week', 
        y='Average_Hours',
        title='Average Study Hours by Day of the Week',
        labels={'Day_of_Week': 'Day of the Week', 'Average_Hours': 'Average Hours'},
        text=average_hours_per_weekday['Average_Hours'].apply(lambda x: f"{x:.2f}"),  # Format text to 2 decimals
        color='Average_Hours',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig_avg_weekday.update_layout(
        title_font=dict(size=24),
        xaxis_title_font=dict(size=18),
        yaxis_title_font=dict(size=18),
        legend=dict(title_font=dict(size=16), font=dict(size=14)),
        width=1600, 
        height=450
    )
    st.plotly_chart(fig_avg_weekday)

    # Add margin top for the donut charts

    st.markdown(f"<h3 style='font-size: 35px; margin-top: 5px;'>Time of the Day Breakdown ☀️</h3>", unsafe_allow_html=True)

    # Create columns for the two donut charts
    tod_selected = st.radio("Select Time of Day", ["Morning", "Afternoon", "Night"])
    col1, col2 = st.columns(2)

  
    # Custom color palettes for each time of day
    color_palettes = {
        "Morning": ["#ff7a44", "#FFA07A", "#ffc3ab", "#ffdcce", "#fff8f5"],  # Shades of Light Salmon for Morning
        "Afternoon": ["#198983", "#20B2AA", "#2ed9d0", "#53e0d8", "#8beae5"],  # Shades of Light Sea Green for Afternoon
        "Night": ["#6c19b9", "#8A2BE2", "#a45ae8", "#b981ee", "#d4b1f4"]  # Shades of Blue Violet for Night
    }

    # Radio button for selecting time of day

    # Content for col1
    with col1:
        st.markdown("<h3 style='margin-top: 20px;'>Study Hours Distribution by Time of Day</h3>", unsafe_allow_html=True)  # Streamlit title with top margin
        
        # Group by 'Tod' and sum the 'Hours'
        df_tod = df_filtered.groupby('Tod')['Hours'].sum().reset_index()

        # Fixed colors for each time of day
        tod_colors = {
            "Morning": "#FFA07A",  # Light Salmon
            "Afternoon": "#20B2AA",  # Light Sea Green
            "Night": "#8A2BE2"  # Blue Violet
        }

        # Create a donut chart for 'Tod' distribution
        fig_tod = px.pie(
            df_tod,
            values='Hours',
            names='Tod',
            hole=0.4,
            color='Tod',
            color_discrete_map=tod_colors
        )

        # Update the traces for labels and legend
        fig_tod.update_traces(
            textinfo='label+percent+value',  # Show label, percent, and hours
            textfont_size=16,  # Increase the label font size
            marker=dict(line=dict(color='#000000', width=1.5))  # Add a border for better visibility
        )

        # Update layout for the legend and labels
        fig_tod.update_layout(
            margin=dict(t=30, l=10, r=10, b=10),  # Adjust margins
            legend=dict(
                font=dict(size=14),  # Increase legend font size
                yanchor="top",
                y=1.05,
                xanchor="right",
                x=1.3
            ),
            width=650,
            height=550
        )

        # Display the donut chart
        st.plotly_chart(fig_tod)

    # Content for col2
    with col2:
        st.markdown("<h3 style='margin-top: 20px;'>Study Hours for Selected Time of Day</h3>", unsafe_allow_html=True)  # Streamlit title with top margin
        
        # Filter data based on the selected time of day
        df_filtered_tod = df_filtered[df_filtered['Tod'] == tod_selected]

        # Group by 'Study' and sum the 'Hours' for the selected time of day
        df_subject = df_filtered_tod.groupby('Study')['Hours'].sum().reset_index()

        # Create a donut chart for subject distribution
        fig_subject = px.pie(
            df_subject,
            values='Hours',
            names='Study',
            hole=0.4,
            color_discrete_sequence=color_palettes[tod_selected]  # Use custom shades for the selected time of day
        )

        # Update the traces for labels and legend
        fig_subject.update_traces(
            textinfo='label+percent+value',  # Show label, percent, and hours
            textfont_size=16,  # Increase the label font size
            marker=dict(line=dict(color='#000000', width=1.0))  # Add a border for better visibility
        )

        # Update layout for the legend and labels
        fig_subject.update_layout(
            margin=dict(t=30, l=10, r=10, b=10),  # Adjust margins
            legend=dict(
                font=dict(size=14),  # Increase legend font size
                yanchor="top",
                y=0.6,
                xanchor="right",
                x=1.3
            ),
            width=650,
            height=550
        )

        # Display the donut chart
        st.plotly_chart(fig_subject)



else:
    st.write("No data available.")

