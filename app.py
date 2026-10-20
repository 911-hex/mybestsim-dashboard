import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURATION DE LA PAGE (Design Pro)
st.set_page_config(
    page_title="MyBestSim | Analytics Dashboard",
    page_icon="🌐",
    layout="wide"
)

# CSS Personnalisé pour un look "SaaS Moderne"
st.markdown("""
    <style>
    .stApp {
        background-color: #F0F2F6;
    }
    h1 {
        color: #1E3A8A !important;
        font-family: 'Inter', sans-serif;
        font-weight: 800 !important;
        text-align: center;
    }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stSelectbox, .stMultiselect, .stSlider {
        background-color: #FFFFFF;
        border-radius: 10px;
    }
    .footer {
        text-align: center;
        color: #6B7280;
        font-size: 0.8rem;
        margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TITRE ET HEADER ---
st.markdown("<h1 style='text-align: center;'>🌐 MyBestSim Analytics</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4B5563; font-size: 1.2rem;'>Analyse comparative et optimisation du catalogue eSIM</p>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center;'><hr></div>", unsafe_allow_html=True)

# 2. CHARGEMENT DES DONNÉES
@st.cache_data
def load_data():
    all_files = glob.glob("data/*.csv")
    if not all_files: return None
    df_list = []
    for file in all_files:
        provider_name = os.path.basename(file).replace(".csv", "").replace("_", " ").title()
        try:
            temp_df = pd.read_csv(file)
            temp_df.columns = [col.strip().lower() for col in temp_df.columns]
            price_col = next((col for col in temp_df.columns if 'prix' in col or 'price' in col), None)
            data_col = next((col for col in temp_df.columns if 'data' in col or 'go' in col), None)
            if price_col and data_col:
                temp_df = temp_df.rename(columns={price_col: 'prix', data_col: 'data'})
                final_temp = temp_df[['prix', 'data']].copy()
                final_temp['fournisseur'] = provider_name
                df_list.append(final_temp)
        except: pass
    return pd.concat(df_list, ignore_index=True) if df_list else None

try:
    df = load_data()
    if df is None:
        st.error("❌ Données manquantes. Veuillez placer vos fichiers CSV dans le dossier /data.")
    else:
        df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
        df['data'] = pd.to_numeric(df['data'], errors='coerce')
        df_clean = df.dropna(subset=['prix', 'data'])

        # --- SIDEBAR ---
        st.sidebar.markdown("### 🛠️ Filtres d'Exploration")
        providers = df_clean['fournisseur'].unique().tolist()
        selected_providers = st.sidebar.multiselect("🎯 Fournisseurs", providers, default=providers)

        min_p, max_p = float(df_clean['prix'].min()), float(df_//clean['prix'].max())
        price_range = st.sidebar.slider("💰 Budget (€)", min_p, max_p, (min_p, max_p))

        min_d, max_d = float(df_clean['data'].min()), float(df_clean['data'].max())
        data_range = st.sidebar.slider("📶 Data Minimum (Go)", min_d, max_d, (min_d, max_d))

        filtered_df = df_clean[
            (df_clean['fournisseur'].isin(selected_providers)) &
            (df_clean['prix'] >= price_range[0]) & (df_clean['prix'] <= price_range[1]) &
            (df_clean['data'] >= data_range[0]) & (df_clean['data'] <= data_range[1])
        ]

        # --- SECTION 1 : KPIs ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.metric("Total eSIM", f"{len(filtered_df)}")
        with kpi2:
            st.metric("Offres Premium", f"{len(filtered_df[filtered_df['prix'] > 100])}")
        with kpi3:
            st.metric("Prix Moyen", f"{filtered_df['prix'].mean():.2f} €" if not filtered_df.empty else "0 €")
        with kpi4:
            st.metric("Data Moyenne", f"{filtered_df['data'].mean():.2f} Go" if not filtered_df.empty else "0 Go")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- SECTION 2 : ANALYSE VISUELLE ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("### 📦 Volume par Fournisseur")
            chart_type = st.radio("Vue préférée :", ["Barres", "Cercle", "Ligne"], horizontal=True)
            provider_counts = filtered_df['fournisseur'].value_counts().reset_index()
            provider_counts.columns = ['Fournisseur', 'Nombre']

            if chart_type == "Barres":
                fig = px.bar(provider_counts, x='Fournisseur', y='Nombre', color='Nombre', color_continuous_scale='Blues', text_auto=True)
            elif chart_type == "Cercle":
                fig = px.pie(provider_counts, values='Nombre', names='Fournisseur', hole=0.4)
            else:
                fig = px.line(provider_counts, x='Fournisseur', y='Nombre', markers=True)

            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown("### 💎 Analyse de Rentabilité (Prix/Go)")
            if not filtered_df.empty:
                df_analysis = filtered_df.copy()
                df_analysis['prix_par_go'] = df_analysis['prix'] / df_analysis['data']
                comp_df = df_analysis.groupby('fournisseur')['prix_par_go'].mean().sort_values().reset_index()
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
            final_comp = filtered_df.copy()
            final_comp['prix_par_go'] = final_comp['prix'] / final_comp['data']
            top_value = final_comp.groupby('fournisseur')['prix_par_go'].mean().sort_values().head(3).reset_index()
            top_value.columns = ['Fournisseur', 'Prix Moyen par Go (€)']
            p1, p2, p3 = st.columns(3)
            cols = top_value['Fournisseur'].tolist()
            vals = top_value['Prix Moyen par Go (€)'].tolist()
            if len(cols) >= 3:
                p1.success(f"🥇 **{cols[0]}**\n\n {vals[0]:.2f} €/Go")
                p2.info(f"🥈 **{cols[1]}**\n\n {vals[1]:.2f} €/Go")
                p3.warning(f"🥉 **{cols[2]}**\n\n {vals[2]:.2f} €/Go")

        with st.expander("📋 Accéder au catalogue complet filtré"):
            st.dataframe(filtered_df, use_container_width=True)

        st.markdown("<div class='footer'>MyBestSim Analytics Dashboard © 2024 - Test de Recrutement</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Une erreur critique est survenue : {e}")
