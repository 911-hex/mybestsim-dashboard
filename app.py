import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px

# Configuration de la page
st.set_page_config(
    page_title="MyBestSim - Analytics Pro",
    page_icon="📊",
    layout="wide"
)

# Style CSS personnalisé
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 MyBestSim : Analyse Avancée du Catalogue eSIM")
st.markdown("Outil d'aide à la décision pour l'optimisation du catalogue fournisseu
st.markdown("---")

# 1. CHARGEMENT ET NETTOYAGE DES DONNÉES
@st.cache_data
def load_data():
    all_files = glob.glob("data/*.csv")
    if not all_files:
        return None

    df_list = []
    for file in all_files:
        provider_name = os.path.basename(file).replace(".csv", "").replace("_", " ").
        try:
            temp_df = pd.read_csv(file)
            # Normalisation des colonnes
            temp_df.columns = [col.strip().lower() for col in temp_df.columns]

            # Recherche flexible des colonnes Prix et Data
            price_col = next((col for col in temp_df.columns if 'prix' in col or 'price' in col), None)
            data_col = next((col for col in temp_df.columns if 'data' in col or 'go'

            if price_col and data_col:
                # On renomme et on ne garde que les colonnes utiles
                temp_df = temp_df.rename(columns={price_col: 'prix', data_col: 'data'
                # On crée une copie propre pour éviter les Warning de Pandas
                final_temp = temp_df[['prix', 'data']].copy()
                final_temp['fournisseur'] = provider_name
                df_list.append(final_temp)
        except Exception as e:
            st.error(f"Erreur sur le fichier {file}: {e}")

    return pd.concat(df_list, ignore_index=True) if df_list else None

try:
    df = load_data()

    if df is None:
        st.error("❌ Aucune donnée valide trouvée. Vérifiez que vos fichiers CSV sontta'.")
    else:
        # Conversion numérique et nettoyage
        df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
        df['data'] = pd.to_numeric(df['data'], errors='coerce')
        # On supprime les lignes vides ou "Illimité"
        df_clean = df.dropna(subset=['prix', 'data'])

        # --- SIDEBAR : FILTRES INTERACTIFS ---
        st.sidebar.header("🔍 Filtres d'Analyse")

        providers = df_clean['fournisseur'].unique().tolist()
        selected_providers = st.sidebar.multiselect("Sélectionner Fournisseurs", prov

        min_p, max_p = float(df_clean['prix'].min()), float(df_clean['prix'].max())
        price_range = st.sidebar.slider("Fourchette de Prix (€)", min_p, max_p, (min_p, max_p))

        min_d, max_d = float(df_clean['data'].min()), float(df_clean['data'].max())
        data_range = st.sidebar.slider("Volume de Data (Go)", min_d, max_d, (min_d, m

        filtered_df = df_clean[
            (df_clean['fournisseur'].isin(selected_providers)) &
            (df_clean['prix'] >= price_range[0]) & (df_clean['prix'] <= price_range[1
            (df_clean['data'] >= data_range[0]) & (df_clean['data'] <= data_range[1])
        ]

        # --- KPI'S ---
        st.subheader("📈 Indicateurs Clés")
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric("Total eSIM", f"{len(filtered_df)}")
        with c2:
            expensive_count = len(filtered_df[filtered_df['prix'] > 100])
            st.metric("Produits > 100€", f"{expensive_count}")
        with c3:
            avg_price = filtered_df['prix'].mean() if not filtered_df.empty else 0
            st.metric("Prix Moyen Global", f"{avg_price:.2f} €")
        with c4:
            avg_data = filtered_df['data'].mean() if not filtered_df.empty else 0
            st.metric("Data Moyenne / Carte", f"{avg_data:.2f} Go")

        st.markdown("---")

        # --- ANALYSE VISUELLE ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📦 Répartition des Fournisseurs")
            chart_type = st.selectbox("Type de vue", ["Barres", "Cercle (Pie)", "Ligne"])

            provider_counts = filtered_df['fournisseur'].value_counts().reset_index()
            provider_counts.columns = ['Fournisseur', 'Nombre']

            if chart_type == "Barres":
                fig = px.bar(provider_counts, x='Fournisseur', y='Nombre', color='Fournisseur', text_auto=True)
            elif chart_type == "Cercle (Pie)":
                fig = px.pie(provider_counts, values='Nombre', names='Fournisseur', hole=0.3)
            else:
                fig = px.line(provider_counts, x='Fournisseur', y='Nombre', markers=True)

            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("💎 Analyse de Compétitivité (Prix au Go)")
            if not filtered_df.empty:
                # Création d'une copie pour éviter les warnings
                df_analysis = filtered_df.copy()
                df_analysis['prix_par_go'] = df_analysis['prix'] / df_analysis['data'

                comp_df = df_analysis.groupby('fournisseur')['prix_par_go'].mean().so
                comp_df.columns = ['Fournisseur', 'Prix Moyen par Go (€)']

                fig_comp = px.bar(comp_df, x='Fournisseur', y='Prix Moyen par Go (€)',
                                 color='Prix Moyen par Go (€)',
                                 color_continuous_scale='RdYlGn_r')
                st.plotly_chart(fig_comp, use_container_width=True)
                st.caption("💡 Plus la barre est basse et verte, plus le fournisseur est rentable.")
            else:
                st.warning("Pas assez de données pour l'analyse de prix.")

        # --- RÉSULTATS FINAUX ---
        st.markdown("---")
        st.subheader("🏆 Top 3 : Meilleurs Rapports Prix/Data")
        if not filtered_df.empty:
            # Calcul basé sur le prix moyen par Go
            final_comp = filtered_df.copy()
            final_comp['prix_par_go'] = final_comp['prix'] / final_comp['data']
            top_value = final_comp.groupby('fournisseur')['prix_par_go'].mean().sort_ex()
            top_value.columns = ['Fournisseur', 'Prix Moyen par Go (€)']
            st.table(top_value)

        with st.expander("👁️ Explorer les données brutes filtrées"):
            st.dataframe(filtered_df)

except Exception as e:
    st.error(f"Une erreur est survenue : {e}")
