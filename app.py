import streamlit as st
import pandas as pd
import glob
import os

# Configuration de la page
st.set_page_config(page_title="MyBestSim - Analyse Catalogue eSIM", layout="wide")

st.title("📊 Dashboard Analyse Catalogue MyBestSim")
st.markdown("---")

# 1. CHARGEMENT ET NETTOYAGE DES DONNÉES
@st.cache_data
def load_data():
    # On cherche tous les fichiers CSV dans le dossier /data
    all_files = glob.glob("data/*.csv")
    if not all_files:
        return None

    df_list = []

    for file in all_files:
        # On extrait le nom du fournisseur depuis le nom du fichier pour plus de sécurité
        provider_name = os.path.basename(file).replace(".csv", "").replace("_", " ").title()

        try:
            # Lecture du CSV
            temp_df = pd.read_csv(file)

            # On vérifie que les colonnes nécessaires existent
            if 'price' in temp_df.columns and 'data_gb' in temp_df.columns:
                # On ne garde que les colonnes utiles pour le calcul
                # On ajoute le nom du fournisseur extrait du fichier
                temp_df = temp_df[['price', 'data_gb']].copy()
                temp_df['fournisseur'] = provider_name
                df_list.append(temp_df)
            else:
                st.warning(f"Le fichier {file} a été ignoré (colonnes 'price' ou 'data_gb' manquantes).")
        except Exception as e:
            st.error(f"Erreur lors de la lecture de {file} : {e}")

    if not df_list:
        return None

    return pd.concat(df_list, ignore_index=True)

try:
    df = load_data()

    if df is None:
        st.error("Aucune donnée valide trouvée. Assurez-vous que vos fichiers CSV sont dans le dossier '/data'.")
    else:
        # --- NETTOYAGE DES TYPES ---
        # Conversion forcée en numérique (remplace les erreurs par NaN)
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['data_gb'] = pd.to_numeric(df['data_gb'], errors='coerce')

        # On supprime les lignes où le prix ou la data sont manquants (ex: les cartes "Illimité")
        # Note : Pour un vrai projet, on pourrait remplacer "Illimité" par une valeur très haute
        df_clean = df.dropna(subset=['price', 'data_gb'])

        # --- SIDEBAR : FILTRES ---
        st.sidebar.header("🔍 Filtres")
        providers = df_clean['fournisseur'].unique().tolist()
        selected_provider = st.sidebar.multiselect("Filtrer par fournisseur", providers, default=providers)

        # Filtrage des données
        filtered_df = df_clean[df_clean['fournisseur'].isin(selected_provider)]

        # --- KPI'S (METRICS) ---
        st.subheader("📈 Indicateurs Clés")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total eSIM", f"{len(filtered_df)}")
        with col2:
            expensive_count = len(filtered_df[filtered_df['price'] > 100])
            st.metric("Produits > 100€", f"{expensive_count}")
        with col3:
            avg_price = filtered_df['price'].mean()
            st.metric("Prix Moyen", f"{avg_price:.2f} €")
        with col4:
            avg_data = filtered_df['data_gb'].mean()
            st.metric("Data Moyenne", f"{avg_data:.2f} Go")

        st.markdown("---")

        # --- ANALYSE DÉTAILLÉE ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("💰 Fourchette de Prix")
            if not filtered_df.empty:
                min_price = filtered_df['price'].min()
                max_price = filtered_df['price'].max()
                st.info(f"Le prix varie de **{min_price:.2f} €** à **{max_price:.2f} €**")
            else:
                st.warning("Aucune donnée pour ce filtre.")

            st.subheader("📦 Répartition par Fournisseur")
            provider_counts = filtered_df['fournisseur'].value_counts()
            st.bar_chart(provider_counts)

        with col_right:
            st.subheader("🌟 Bonus : Analyse Performance")
            if not filtered_df.empty:
                # Top 3 fournisseurs les moins chers en moyenne
                top_providers = filtered_df.groupby('fournisseur')['price'].mean().sort_values().head(3)
                st.write("🏆 **Top 3 Fournisseurs les plus compétitifs (Prix Moyen) :**")
                st.dataframe(top_providers)
            else:
                st.warning("Aucune donnée pour ce filtre.")

        # --- TABLEAU DE DONNÉES ---
        with st.expander("👁️ Voir les données brutes"):
            st.dataframe(filtered_df)

except Exception as e:
    st.error(f"Erreur fatale lors de l'exécution : {e}")
