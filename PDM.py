import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from datetime import datetime, timedelta
import numpy as np

# Configuration de la page
st.set_page_config(page_title="PDM Tracker", layout="wide", page_icon="📈")

# --- STYLE CSS ---
st.markdown("""
    <style>
    /* Style du bloc message d'amour */
    .message-damour {
        background-color: #F5D1D0;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #F5D1D0;
        margin-bottom: 25px;
    }
    .message-damour p, .message-damour h3 {
        color: #000000 !important;
        margin-bottom: 8px;
    }

    /* Style des metrics en bas */
    .stMetric { 
        background-color: rgba(245, 209, 208, 0.3); 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #F5D1D0; 
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Suivi et prédiction PDM")

# --- MESSAGE PERSONNEL (Corrigé pour être rose) ---
st.markdown(f"""
    <div class="message-damour">
        <p>Coucou mon amoureux ❤️</p>
        <p>Comme promis, je t'ai codé un site qui te permet de voir ta progression. C'est super simple à utiliser et tu n'auras pas de difficultés vu que tu es super intelligent, super beau, super musclé, super drôle.</p>
        <p>Si tu as des questions, envoie-moi un snap, j'essayerai de te répondre sous 3 à 5 jours ouvrés.</p>
        <p><Gros kiss, ton amoureuse</p>
    </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("⚙️ Paramètres")

forecast_days = st.sidebar.slider("Nombre de jours à prédire :", 30, 365, 90)
col_a, col_b = st.sidebar.columns(2)
col_a.caption("30 jours")
col_b.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>365 jours</p>", unsafe_allow_html=True)

st.sidebar.divider()

st.sidebar.subheader("Méthode de calcul")
recent_weight = st.sidebar.slider(
    "Pondération", 
    min_value=0, 
    max_value=100, 
    value=50,
    label_visibility="collapsed") / 100

c1, c2 = st.sidebar.columns(2)
c1.caption("Sur tout l'historique")
c2.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>Sur les 30 derniers jours</p>", unsafe_allow_html=True)

# --- ZONE DE SAISIE ---
st.write("")
st.markdown("### 📝 Saisie des données")
st.markdown("**Ici tu colles directement ta note avec tes poids et leurs dates :**")

raw_text = st.text_area(
    "Zone de saisie", 
    placeholder="Exemple :\n19/08/2025 70.2\n20/09/2025 70.5\n21/08/2026 70.7", 
    height=200, 
    label_visibility="collapsed"
)

if raw_text:
    pattern = r"(\d{1,2}/\d{1,2}/\d{2,4}).*?(\d{2,3}[.,]?\d?)"
    matches = re.findall(pattern, raw_text)

    if matches:
        data = []
        for m_date, m_weight in matches:
            try:
                val_weight = float(m_weight.replace(',', '.'))
                clean_date = pd.to_datetime(m_date, dayfirst=True)
                data.append({"Date": clean_date, "Poids": val_weight})
            except:
                continue

        df = pd.DataFrame(data).sort_values("Date")

        if not df.empty and 'Poids' in df.columns:
            df['Poids_Lisse'] = df['Poids'].ewm(span=7).mean()
            
            first_date = df['Date'].min()
            df['DaysPassed'] = (df['Date'] - first_date).dt.days
            m_global, _ = np.polyfit(df['DaysPassed'], df['Poids'], 1)
            
            recent_cutoff = df['Date'].max() - timedelta(days=30)
            recent_df = df[df['Date'] >= recent_cutoff]
            
            if len(recent_df) > 1:
                r_days = (recent_df['Date'] - recent_df['Date'].min()).dt.days
                m_recent, _ = np.polyfit(r_days, recent_df['Poids'], 1)
            else:
                m_recent = m_global 

            m_hybrid = (m_global * (1 - recent_weight)) + (m_recent * recent_weight)

            last_date = df['Date'].max()
            last_weight_smooth = df['Poids_Lisse'].iloc[-1]
            last_weight_real = df['Poids'].iloc[-1]
            
            future_dates = [last_date + timedelta(days=x) for x in range(0, forecast_days + 1)]
            prediction_path = [last_weight_smooth + (m_hybrid * x) for x in range(0, forecast_days + 1)]

            fig = go.Figure()

            # Historique
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['Poids_Lisse'], 
                mode='lines', name='Historique',
                line=dict(color='#ca0201', width=4, shape='spline')
            ))
            
            # Prédiction espacée
            fig.add_trace(go.Scatter(
                x=future_dates[::5], 
                y=prediction_path[::5],
                mode='markers', 
                name='Prédiction',
                marker=dict(color='#ca0201', size=4, symbol='circle')
            ))

            fig.update_layout(
                template="plotly_dark", 
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Date",
                yaxis_title="Poids (kg)",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📊 Statistiques")
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Poids actuel", f"{last_weight_real} kg")
            target_w = prediction_path[-1]
            diff = target_w - last_weight_real
            col_m2.metric(f"Objectif ({forecast_days} j)", f"{target_w:.1f} kg", f"{diff:+.1f} kg")
            weekly_rate = (m_hybrid * 7)
            col_m3.metric("Vitesse actuelle", f"{weekly_rate:+.2f} kg / sem")
    else:
        st.info("💡 J'attends tes données... Copie-les au format 'Date Poids' !")
