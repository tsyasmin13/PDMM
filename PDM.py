import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="PDM Tracker", layout="wide")
st.title("Suivi et prédiction PDM")

# --- SIDEBAR ---
st.sidebar.header("Paramètres")
forecast_days = st.sidebar.slider("Prédiction sur X jours", 30, 365, 90)
# Weighting: 0 is pure Global average, 100 is pure Recent (last 30 days)
recent_weight = st.sidebar.slider("Je pondere la prédiction", 0, 100, 50) / 100

raw_text = st.text_area("Je colle mes poids avec leur date ici :", height=200)

if raw_text:
    # Regex to find DD/MM/YYYY and the weight number
    pattern = r"(\d{1,2}/\d{1,2}/\d{4}).*?(\d{2,3}\.?\d?)"
    matches = re.findall(pattern, raw_text)

    if matches:
        data = []
        for m_date, m_weight in matches:
            try:
                clean_date = pd.to_datetime(m_date, dayfirst=True)
                data.append({"Date": clean_date, "Poids": float(m_weight)})
            except:
                continue

        df = pd.DataFrame(data).sort_values("Date")

        if not df.empty:
            # --- 1. CALCULATE HYBRID SLOPE ---
            # Global Slope
            first_date = df['Date'].min()
            df['DaysPassed'] = (df['Date'] - first_date).dt.days
            m_global, _ = np.polyfit(df['DaysPassed'], df['Weight'], 1)
            
            # Recent Slope (Last 30 Days)
            recent_df = df[df['Date'] > (df['Date'].max() - timedelta(days=30))]
            if len(recent_df) > 1:
                recent_days = (recent_df['Date'] - recent_df['Date'].min()).dt.days
                m_recent, _ = np.polyfit(recent_days, recent_df['Weight'], 1)
            else:
                m_recent = m_global 

            # Hybrid Calculation
            m_hybrid = (m_global * (1 - recent_weight)) + (m_recent * recent_weight)

            # --- 2. GENERATE FORECAST ---
            last_date = df['Date'].max()
            last_weight = df['Weight'].iloc[-1]
            future_dates = [last_date + timedelta(days=x) for x in range(0, forecast_days + 1)]
            prediction_path = [last_weight + (m_hybrid * x) for x in range(0, forecast_days + 1)]

            # --- 3. PLOTTING ---
            fig = go.Figure()

            # HISTORY: Blue Line Plot
            fig.add_trace(go.Scatter(
                x=df['Date'], 
                y=df['Weight'], 
                mode='lines+markers', 
                name='History',
                line=dict(color='#1f77b4', width=3), # Standard Blue
                marker=dict(size=4, opacity=0.6)
            ))
            
            # PREDICTION: Green Line with Small Dots
            fig.add_trace(go.Scatter(
                x=future_dates, 
                y=prediction_path, 
                mode='lines+markers', 
                name='Prediction',
                line=dict(color='#2ca02c', width=3, dash='dot'), # Green Dotted
                marker=dict(size=5, symbol='circle')
            ))

            fig.update_layout(
                template="plotly_dark", 
                title="Weight Journey",
                xaxis_title="Date",
                yaxis_title="Weight (kg)",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)

            # --- METRICS ---
            st.write("### Stats")
            col1, col2 = st.columns(2)
            col1.metric("Current weight", f"{last_weight} kg")
            col2.metric(f"Projected ({forecast_days} days)", f"{prediction_path[-1]:.1f} kg", f"{prediction_path[-1]-last_weight:+.1f} kg")

    else:
        st.info("Paste your data to see the graph!")
