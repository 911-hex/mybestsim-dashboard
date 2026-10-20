import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="MyBestSim - Analytics Pro", layout="wide")

st.title("📊 MyBestSim : Analyse Avancée du Catalogue eSIM")
st.markdown("---")

# 1. CHARGEMENT ET NETTOYAGE DES DONNÉES
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
            # Normalisation des colonnes
            temp_df.columns = [col.strip().lower() for col in temp_df.columns]
            price_col = next((col for col in temp_df.columns if 'prix' in col or 'price' in col), None)
            data_col = next((col for col in temp_df.columns if 'data' in col or 'go' in col), None)

            if price_col and data_col:
                temp_df = temp_df.rename(columns={price_col: 'prix', data_col: 'data'})
                temp_df = temp_df[['prix', 'data']].copy()
                temp_df['fournisseur'] = provider_name
                df_list.append(temp_df)
        except Exception as e:
            st.error(f"Erreur sur {file}: {e}")

    return pd.concat(df_list, ignore_index=True) if df_list else None

try:
    df = load_data()

    if df is None:
        st.error("Aucune donnée valide trouvée. Vérifiez le dossier /data.")
    else:
        # Conversion numérique et nettoyage
        df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
        df['data'] = pd.to_numeric(df['data'], errors='coerce')
        df = df.dropna(subset=['prix', 'data'])

        # --- SIDEBAR : FILTRES AVANCÉS ---
        st.sidebar.header("🔍 Filtres d'Analyse")

        # Filtre Fournisseur
        providers = df['fournisseur'].unique().tolist()
        selected_providers = st.sidebar.multiselect("Fournisseurs", providers, default=providers)

        # Filtre de Prix (Slider)
        min_p, max_p = float(df['prix'].min()), float(df['prix'].max())
        price_range = st.sidebar.slider("Fourchette de Prix (€)", min_p, max_p, (min_p, max_p))

        # Filtre de Data (Slider)
        min_d, max_d = float(df['data'].min()), float(df['data'].max())
        data_range = st.sidebar.slider("Volume de Data (Go)", min_d, max_d, (min_d, max_d))

        # Application des filtres
        filtered_df = df[
            (df['fournisseur'].isin(selected_providers)) &
            (df['prix'] >= price_range[0]) & (df['prix'] <= price_range[1]) &
            (df['data'] >= data_range[0]) & (df['data'] <= data_range[1])
        ]

        # --- KPI'S ---
        st.subheader("📈 Indicateurs Clés")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total eSIM", f"{len(filtered_df)}")
        c2.metric("Produits > 100€", f"{len(filtered_df[filtered_df['prix'] > 100])}")
        c3.metric("Prix Moyen", f"{filtered_df['prix'].mean():.2f} €")
        c4.metric("Data Moyenne", f"{filtered_df['data'].mean():.2f} Go")

        st.markdown("---")

        # --- GRAPHIQUES DYNAMIQUES ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📦 Répartition des Fournisseurs")
            chart_type = st.selectbox("Choisir le type de graphique", ["Barres", "Cercle (Pie)", "Ligne"])

            provider_counts = filtered_df['fournisseur'].value_counts().reset_index()
            provider_counts.columns = ['Fournisseur', 'Nombre']

            if chart_type == "Barres":
                fig = px.bar(provider_counts, x='Fournisseur', y='Nombre', color='Fournisseur')
            elif chart_type == "Cercle (Pie)":
                fig = px.pie(provider_counts, values='Nombre', names='Fournisseur')
            else:
                fig = px.line(provider_counts, x='Fournisseur', y='Nombre', markers=True)

            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("💰 Analyse Prix vs Data")
            # Scatter plot pour voir la corrélation
            fig_scatter = px.scatter(filtered_df, x='data', y='prix', color='fournisseur',
                                    hover_data=['fournisseur'], labels={'data': 'Data (Go)', 'prix': 'Prix (€)'})
            st.plotly_chart(fig_scatter, use_container_width=True)

        # --- BONUS : TABLEAU COMPARATIF ---
        st.markdown("---")
        st.subheader("🏆 Top 3 Fournisseurs les plus compétitifs")
        top_3 = filtered_df.groupby('fournisseur')['prix'].mean().sort_values().head(3).reset_index()
        top_3.columns = ['Fournisseur', 'Prix Moyen (€)']
        st.table(top_3)

        with st.expander("👁️ Explorer les données filtrées"):
            st.dataframe(filtered_df)

except Exception as e:
    st.error(f"Erreur : {e}")
