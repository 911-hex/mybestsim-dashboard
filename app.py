import streamlit as st
import pandas as pd
import glob
import os

# Configuration de la page
st.set_page_config(page_title="MyBestSim - Analyse Catalogue eSIM", layout="wide")

st.title("📊 Dashboard Analyse Catalogue MyBestSim")
st.markdown("---")

# 1. CHARGEMENT DES DONNÉES
@st.cache_data # Optimise le chargement pour ne pas relire les fichiers à chaque clic
def load_data():
    all_files = glob.glob("data/*.csv") # Assure-toi que tes CSV sont dans un dossier /data
    df_list = []

    for file in all_files:
        # On extrait le nom du fournisseur depuis le nom du fichier
        provider = os.path.basename(file).replace(".csv", "").replace("_", " ").title()
        temp_df = pd.read_csv(file)
        temp_df['Fournisseur'] = provider
        df_list.append(temp_df)

    return pd.concat(df_list, ignore_index=True)

try:
    df = load_data()

    # --- SIDEBAR : FILTRES ---
    st.sidebar.header("🔍 Filtres")
    providers = df['Fournisseur'].unique().tolist()
    selected_provider = st.sidebar.multiselect("Filtrer par fournisseur", providers, default=providers)

    # Filtrage des données
    filtered_df = df[df['Fournisseur'].isin(selected_provider)]

    # --- KPI'S (METRICS) ---
    st.subheader("📈 Indicateurs Clés")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total eSIM", f"{len(filtered_df)}")
    with col2:
        expensive_count = len(filtered_df[filtered_df['Prix'] > 100])
        st.metric("Produits > 100€", f"{expensive_count}")
    with col3:
        avg_price = filtered_df['Prix'].mean()
        st.metric("Prix Moyen", f"{avg_price:.2f} €")
    with col4:
        avg_data = filtered_df['Data (Go)'].mean()
        st.metric("Data Moyenne", f"{avg_data:.2f} Go")

    st.markdown("---")

    # --- ANALYSE DÉTAILLÉE ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("💰 Fourchette de Prix")
        min_price = filtered_df['Prix'].min()
        max_price = filtered_df['Prix'].max()
        st.info(f"Le prix varie de **{min_price} €** à **{max_price} €**")

        st.subheader("📦 Répartition par Fournisseur")
        provider_counts = filtered_df['Fournisseur'].value_counts()
        st.bar_chart(provider_counts)

    with col_right:
        st.subheader("🌟 Bonus : Analyse Performance")
        # Top 3 fournisseurs les moins chers
        top_providers = filtered_df.groupby('Fournisseur')['Prix'].mean().sort_values().head(3)
        st.write("🏆 **Top 3 Fournisseurs les plus compétitifs :**")
        st.dataframe(top_providers)

    # --- TABLEAU DE DONNÉES ---
    with st.expander("👁️ Voir les données brutes"):
        st.dataframe(filtered_df)

except Exception as e:
    st.error(f"Erreur lors du chargement des données : {e}")
    st.info("Vérifiez que vos fichiers CSV sont bien placés dans un dossier nommé 'data' à la racine du projet.")
