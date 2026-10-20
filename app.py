import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px
import google.generativeai as genai

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="MyBestSim | AI Analytics",
    page_icon="🤖",
    layout="wide"
)

# Configuration de l'API Gemini
GEMINI_API_KEY = "AQ.Ab8RN6IXuLtuPY4O5xgnTea_yLJzBMOhgvo3wgV5CO6Clf-kVg"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.0-pro')

# CSS Personnalisé
st.markdown("""
    <style>
    .stApp { background-color: #F0F2F6; }
    h1 { color: #1E3A8A !important; font-family: 'Inter', sans-serif; font-weight: 800 !important; text-align: center; }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF; border: 1px solid #E5E7EB; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .ai-box {
        background-color: #EEF2FF; border-left: 5px solid #4F46E5; padding: 20px; border-radius: 10px; margin-bottom: 20px;
    }
    .footer { text-align: center; color: #6B7280; font-size: 0.8rem; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>🤖 MyBestSim AI Analytics</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4B5563; font-size: 1.2rem;'>Analyse intelligente et optimisation du catalogue eSIM</p>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center;'><hr></div>", unsafe_allow_html=True)

# 2. CHARGEMENT DES DONNÉES
@st.cache_data
def load_data():
    all_files = glob.glob("data/*.csv")
    if not all_files:
        return None
    df_list = []
    for file in all_files:
        provider_name = os.path.basename(file).replace(".csv", "").replace("_", " ").title()
        try:
            temp_df = pd.read_csv(file)
            temp_df.columns = [col.strip().lower() for col in temp_df.columns]
            price_col = next((col for col in temp_df.columns if 'prix' in col or 'price' in col), None)
            data_col = next((col for col in temp_df.columns if 'data' in col or 'go' in col), None)
            if price_col and data_col:
                clean_temp = pd.DataFrame()
                clean_temp['prix'] = temp_df[price_col]
                clean_temp['data'] = temp_df[data_col]
                clean_temp['fournisseur'] = provider_name
                df_list.append(clean_temp)
        except:
            pass
    return pd.concat(df_list, ignore_index=True) if df_list else None

try:
    df_raw = load_data()
    if df_raw is None:
        st.error("❌ Données manquantes. Vérifiez le dossier /data.")
    else:
        df_raw['prix'] = pd.to_numeric(df_raw['prix'], errors='coerce')
        df_raw['data'] = pd.to_numeric(df_raw['data'], errors='coerce')
        df_final = df_raw.dropna(subset=['prix', 'data']).copy()

        # --- SIDEBAR ---
        st.sidebar.markdown("### 🛠️ Filtres d'Exploration")
        providers = df_final['fournisseur'].unique().tolist()
        selected_providers = st.sidebar.multiselect("🎯 Fournisseurs", providers, default=providers)

        min_p, max_p = float(df_final['prix'].min()), float(df_final['prix'].max())
        price_range = st.sidebar.slider("💰 Budget (€)", min_p, max_p, (min_p, max_p))

        min_d, max_d = float(df_final['data'].min()), float(df_final['data'].max())
        data_range = st.sidebar.slider("📶 Data Minimum (Go)", min_d, max_d, (min_d, max_d))

        mask = (
            (df_final['fournisseur'].isin(selected_providers)) &
            (df_final['prix'] >= price_range[0]) & (df_final['prix'] <= price_range[1]) &
            (df_final['data'] >= data_range[0]) & (df_final['data'] <= data_range[1])
        )
        filtered_df = df_final[mask].copy()

        # --- SECTION 1 : KPIs ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.metric("Total eSIM", f"{len(filtered_df)}")
        with kpi2:
            st.metric("Offres Premium", f"{len(filtered_df[filtered_df['prix'] > 100])}")
        with kpi3:
            avg_p = filtered_df['prix'].mean() if not filtered_df.empty else 0
            st.metric("Prix Moyen", f"{avg_p:.2f} €")
        with kpi4:
            avg_d = filtered_df['data'].mean() if not filtered_df.empty else 0
            st.metric("Data Moyenne", f"{avg_d:.2f} Go")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- SECTION 2 : ANALYSE VISUELLE ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("### 📦 Volume par Fournisseur")
            chart_type = st.radio("Vue préférée :", ["Barres", "Cercle", "Ligne"], horizontal=True)
            counts = filtered_df['fournisseur'].value_counts().reset_index()
            counts.columns = ['Fournisseur', 'Nombre']
            if chart_type == "Barres":
                fig = px.bar(counts, x='Fournisseur', y='Nombre', color='Nombre', color_continuous_scale='Blues', text_auto=True)
            elif chart_type == "Cercle":
                fig = px.pie(counts, values='Nombre', names='Fournisseur', hole=0.4)
            else:
                fig = px.line(counts, x='Fournisseur', y='Nombre', markers=True)
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown("### 💎 Analyse de Rentabilité (Prix/Go)")
            if not filtered_df.empty:
                filtered_df['prix_par_go'] = filtered_df['prix'] / filtered_df['data']
                comp_df = filtered_df.groupby('fournisseur')['prix_par_go'].mean().sort_values().reset_index()
                comp_df.columns = ['Fournisseur', 'Prix Moyen par Go (€)']
                fig_comp = px.bar(comp_df, x='Prix Moyen par Go (€)', y='Fournisseur', orientation='h',
                                 color='Prix Moyen par Go (€)', color_continuous_scale='RdYlGn_r', text_auto='.2f')
                fig_comp.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=20, b=20),
                                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.warning("Pas assez de données.")

        # --- SECTION 3 : TOP PERFORMANCE ---
        st.markdown("<br><div style='text-align: center;'><hr></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>🏆 Top 3 : Meilleure Valeur Ajoutée</h3>", unsafe_allow_html=True)

        if not filtered_df.empty:
            top_val = filtered_df.groupby('fournisseur')['prix_par_go'].mean().sort_values().head(3).reset_index()
            top_val.columns = ['Fournisseur', 'Prix Moyen par Go (€)']
            p1, p2, p3 = st.columns(3)
            c_list = top_val['Fournisseur'].tolist()
            v_list = top_val['Prix Moyen par Go (€)'].tolist()
            if len(c_list) >= 1: p1.success(f"🥇 **{c_list[0]}**\n\n {v_list[0]:.2f} €/Go")
            if len(c_list) >= 2: p2.info(f"🥈 **{c_list[1]}**\n\n {v_list[1]:.2f} €/Go")
            if len(c_list) >= 3: p3.warning(f"🥉 **{c_list[2]}**\n\n {v_list[2]:.2f} €/Go")

        # --- SECTION 4 : L'AGENT IA (Gemini) ---
        st.markdown("<br><div style='text-align: center;'><hr></div>", unsafe_allow_html=True)
        st.markdown("### 🤖 Assistant IA MyBestSim")
        st.markdown("Posez une question sur vos données pour obtenir une analyse instantanée.")

        user_question = st.text_input("Votre question ici...", placeholder="Ex: Quelle est la meilleure offre pour un voyageur budget ?")

        if user_question:
            with st.spinner("L'IA analyse vos données..."):
                # Préparation du contexte pour Gemini
                # On envoie un échantillon représentatif des données filtrées
                data_context = filtered_df.to_string() if len(filtered_df) < 50 else filtered_df.describe().to_string()

                prompt = f"""
                Tu es l'expert data de MyBestSim. Voici les données actuelles du catalogue eSIM :
                {data_context}

                Question de l'utilisateur : {user_question}

                Réponds de manière professionnelle, concise et apporte une valeur ajoutée business.
                Si la réponse se trouve dans les données, cite des chiffres précis.
                """

                try:
                    response = model.generate_content(prompt)
                    st.markdown(f"<div class='ai-box'>{response.text}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Erreur IA : {e}")

        with st.expander("📋 Accéder au catalogue complet filtré"):
            st.dataframe(filtered_df, use_container_width=True)

        st.markdown("<div class='footer'>MyBestSim AI Analytics Dashboard © 2024 - Test de Recrutement</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Une erreur critique est survenue : {e}")
