
import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px
import google.generativeai as genai
import json

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="MyBestSim | AI Analytics",
    page_icon="🤖",
    layout="wide"
)

# Configuration de l'API Gemini
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3.8-flash")

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


# En-tête avec logo à gauche et titres conservés
from pathlib import Path

col_logo, col_titre = st.columns([1, 5])

with col_logo:
    logo_path = Path(__file__).parent / "logo mybestsim.png"
    if logo_path.exists():
        st.image(str(logo_path), width=150)

with col_titre:
    st.markdown(
        "<h1 style='text-align: center;'>🤖 MyBestSim AI Analytics</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; color: #4B5563; font-size: 1.2rem;'>"
        "Analyse intelligente et optimisation du catalogue eSIM</p>",
        unsafe_allow_html=True
    )

st.markdown("<div style='text-align: center;'><hr></div>", unsafe_allow_html=True)


# 2. CHARGEMENT DES DONNÉES

# 2. CHARGEMENT DES DONNÉES
@st.cache_data
def load_data():
    all_files = glob.glob("data/*.csv")

    if not all_files:
        return None

    df_list = []

    for file in all_files:
        provider_name = (
            os.path.basename(file)
            .replace(".csv", "")
            .replace("_", " ")
            .title()
        )

        try:
            temp_df = pd.read_csv(file)
            temp_df.columns = [
                str(col).strip().lower() for col in temp_df.columns
            ]

            # Conserver toutes les colonnes du CSV
            clean_temp = temp_df.copy()

            # Fournisseur
            if "provider" not in clean_temp.columns:
                clean_temp["provider"] = provider_name

            clean_temp["provider"] = (
                clean_temp["provider"]
                .fillna(provider_name)
                .astype(str)
                .str.strip()
            )
            clean_temp["fournisseur"] = clean_temp["provider"]

            # Prix
            if "price" not in clean_temp.columns:
                price_col = next(
                    (
                        c for c in clean_temp.columns
                        if "prix" in c or "price" in c
                    ),
                    None
                )
                clean_temp["price"] = (
                    clean_temp[price_col] if price_col else pd.NA
                )

            clean_temp["price"] = pd.to_numeric(
                clean_temp["price"].astype(str).str.replace(
                    ",", ".", regex=False
                ),
                errors="coerce"
            )
            clean_temp["prix"] = clean_temp["price"]

            # Volume de données en Go
            if "data_gb" not in clean_temp.columns:
                data_col = next(
                    (
                        c for c in clean_temp.columns
                        if c in ("data", "go", "data_go")
                    ),
                    None
                )
                clean_temp["data_gb"] = (
                    clean_temp[data_col] if data_col else pd.NA
                )

            clean_temp["data_gb"] = pd.to_numeric(
                clean_temp["data_gb"].astype(str).str.replace(
                    ",", ".", regex=False
                ),
                errors="coerce"
            )
            clean_temp["data"] = clean_temp["data_gb"]

            # Validité
            if "validity_days" not in clean_temp.columns:
                clean_temp["validity_days"] = pd.NA

            clean_temp["validity_days"] = pd.to_numeric(
                clean_temp["validity_days"], errors="coerce"
            )

            # Colonnes facultatives
            optional_columns = [
                "sku", "product_name", "country_code",
                "country_name", "data_display", "currency",
                "network", "top_up"
            ]

            for col in optional_columns:
                if col not in clean_temp.columns:
                    clean_temp[col] = pd.NA

            df_list.append(clean_temp)

        except (
            OSError,
            pd.errors.ParserError,
            UnicodeDecodeError
        ) as e:
            st.warning(f"Impossible de lire {file} : {e}")

    if not df_list:
        return None

    return pd.concat(df_list, ignore_index=True, sort=False)



try:
    df_raw = load_data()

    if df_raw is None:
        st.error("❌ Données manquantes. Vérifiez le dossier /data.")
    else:
        df_raw["prix"] = pd.to_numeric(df_raw["prix"], errors="coerce")
        df_raw["data"] = pd.to_numeric(df_raw["data"], errors="coerce")
        df_raw["price"] = df_raw["prix"]
        df_raw["data_gb"] = df_raw["data"]

        # Conserver les offres même si certaines données facultatives manquent.
        #         Les filtres numériques ignoreront les valeurs manquantes.
        df_final = df_raw.dropna(subset=["prix"]).copy()
        
# --- SIDEBAR : FILTRES eSIM ---
st.sidebar.markdown("## 🌍 Explorer les offres eSIM")
st.sidebar.caption("Affinez les résultats selon votre voyage.")

# Normaliser les colonnes de texte utilisées dans les filtres
for col in ["provider", "country_name", "network"]:
    if col in df_final.columns:
        df_final[col] = df_final[col].fillna("").astype(str).str.strip()

# Fournisseurs
with st.sidebar.expander("🏢 Fournisseurs", expanded=True):
    providers = sorted(
        p for p in df_final["provider"].unique() if p
    )

    selected_providers = st.multiselect(
        "Choisir les fournisseurs",
        options=providers,
        default=providers,
        key="filter_providers"
    )

# Pays
with st.sidebar.expander("🌎 Pays / Destination", expanded=False):
    countries = sorted(
        p for p in df_final["country_name"].unique() if p
    )

    selected_countries = st.multiselect(
        "Choisir un ou plusieurs pays",
        options=countries,
        default=[],
        placeholder="Rechercher un pays...",
        key="filter_countries"
    )

# Technologie réseau
with st.sidebar.expander("📶 Réseau mobile", expanded=False):
    network_text = df_final["network"].str.upper()

    network_options = []
    if network_text.str.contains(r"4G|LTE", regex=True).any():
        network_options.append("4G")
    if network_text.str.contains("5G", regex=False).any():
        network_options.append("5G")

    selected_networks = st.multiselect(
        "Technologie",
        options=network_options,
        default=[],
        key="filter_networks"
    )

# Budget
with st.sidebar.expander("💰 Budget", expanded=False):
    prices = df_final["price"].dropna()

    if not prices.empty:
        pmin, pmax = float(prices.min()), float(prices.max())

        if pmin < pmax:
            price_range = st.slider(
                "Prix",
                min_value=pmin,
                max_value=pmax,
                value=(pmin, pmax),
                key="filter_price"
            )
        else:
            price_range = (pmin, pmax)
    else:
        price_range = None

# Volume de données
with st.sidebar.expander("📊 Volume de données", expanded=False):
    data_values = df_final["data_gb"].dropna()

    if not data_values.empty:
        dmin, dmax = float(data_values.min()), float(data_values.max())

        if dmin < dmax:
            data_range = st.slider(
                "Data incluse (Go)",
                min_value=dmin,
                max_value=dmax,
                value=(dmin, dmax),
                key="filter_data"
            )
        else:
            data_range = (dmin, dmax)
    else:
        data_range = None

# Durée de validité
with st.sidebar.expander("📅 Durée de validité", expanded=False):
    validity_values = df_final["validity_days"].dropna()

    if not validity_values.empty:
        vmin = int(validity_values.min())
        vmax = int(validity_values.max())

        if vmin < vmax:
            validity_range = st.slider(
                "Validité (jours)",
                min_value=vmin,
                max_value=vmax,
                value=(vmin, vmax),
                key="filter_validity"
            )
        else:
            validity_range = (vmin, vmax)
    else:
        validity_range = None

# Recharge possible
with st.sidebar.expander("🔄 Options", expanded=False):
    top_up_filter = st.selectbox(
        "Recharge possible",
        options=["Toutes les offres", "Oui", "Non"],
        key="filter_topup"
    )

# --- APPLICATION DES FILTRES ---
filtered_df = df_final.copy()

# Fournisseurs
if selected_providers:
    filtered_df = filtered_df[
        filtered_df["provider"].isin(selected_providers)
    ]
else:
    filtered_df = filtered_df.iloc[0:0]

# Pays : aucun pays sélectionné signifie tous les pays
if selected_countries:
    filtered_df = filtered_df[
        filtered_df["country_name"].isin(selected_countries)
    ]

# Réseau 4G / 5G
if selected_networks:
    network_text = filtered_df["network"].str.upper()
    network_mask = pd.Series(False, index=filtered_df.index)

    if "4G" in selected_networks:
        network_mask |= network_text.str.contains(
            r"4G|LTE", regex=True
        )

    if "5G" in selected_networks:
        network_mask |= network_text.str.contains(
            "5G", regex=False
        )

    filtered_df = filtered_df[network_mask]

# Budget
if price_range is not None:
    filtered_df = filtered_df[
        filtered_df["price"].between(*price_range)
    ]

# Volume de données : les valeurs manquantes ne correspondent pas au filtre
if data_range is not None:
    filtered_df = filtered_df[
        filtered_df["data_gb"].between(*data_range)
    ]

# Validité
if validity_range is not None:
    filtered_df = filtered_df[
        filtered_df["validity_days"].between(*validity_range)
    ]

# Recharge
if top_up_filter != "Toutes les offres":
    top_up_values = (
        filtered_df["top_up"].astype(str).str.strip().str.lower()
    )

    true_values = {"true", "1", "yes", "oui", "y"}
    false_values = {"false", "0", "no", "non", "n"}

    if top_up_filter == "Oui":
        filtered_df = filtered_df[top_up_values.isin(true_values)]
    else:
        filtered_df = filtered_df[top_up_values.isin(false_values)]

st.sidebar.caption(
    f"🎯 {len(filtered_df):,} offres correspondent aux filtres."
)


        # Supprimer les anciennes données en cache après modification du chargement





    
        

        # --- SECTION 1 : KPIs ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            st.metric("Total eSIM", f"{len(filtered_df)}")

        with kpi2:
            st.metric(
                "Offres Premium",
                f"{len(filtered_df[filtered_df['prix'] > 100])}"
            )

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
            chart_type = st.radio(
                "Vue préférée :", ["Barres", "Cercle", "Ligne"],
                horizontal=True
            )

            counts = filtered_df['fournisseur'].value_counts().reset_index()
            counts.columns = ['Fournisseur', 'Nombre']

            if chart_type == "Barres":
                fig = px.bar(
                    counts, x='Fournisseur', y='Nombre',
                    color='Nombre', color_continuous_scale='Blues',
                    text_auto=True
                )
            elif chart_type == "Cercle":
                fig = px.pie(
                    counts, values='Nombre', names='Fournisseur', hole=0.4
                )
            else:
                fig = px.line(
                    counts, x='Fournisseur', y='Nombre', markers=True
                )

            fig.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown("### 💎 Analyse de Rentabilité (Prix/Go)")

            if not filtered_df.empty:
                filtered_df['prix_par_go'] = (
                    filtered_df['prix'] / filtered_df['data']
                )

                comp_df = (
                    filtered_df.groupby('fournisseur')['prix_par_go']
                    .mean()
                    .sort_values()
                    .reset_index()
                )
                comp_df.columns = ['Fournisseur', 'Prix Moyen par Go (€)']

                fig_comp = px.bar(
                    comp_df,
                    x='Prix Moyen par Go (€)',
                    y='Fournisseur',
                    orientation='h',
                    color='Prix Moyen par Go (€)',
                    color_continuous_scale='RdYlGn_r',
                    text_auto='.2f'
                )

                fig_comp.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    margin=dict(l=20, r=20, t=20, b=20),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.warning("Pas assez de données.")

        # --- SECTION 3 : TOP PERFORMANCE ---
        st.markdown(
            "<br><div style='text-align: center;'><hr></div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<h3 style='text-align: center;'>🏆 Top 3 : Meilleure Valeur Ajoutée</h3>",
            unsafe_allow_html=True
        )

        if not filtered_df.empty:
            top_val = (
                filtered_df.groupby('fournisseur')['prix_par_go']
                .mean()
                .sort_values()
                .head(3)
                .reset_index()
            )
            top_val.columns = ['Fournisseur', 'Prix Moyen par Go (€)']

            p1, p2, p3 = st.columns(3)
            c_list = top_val['Fournisseur'].tolist()
            v_list = top_val['Prix Moyen par Go (€)'].tolist()

            if len(c_list) >= 1:
                p1.success(f"🥇 **{c_list[0]}**\n\n {v_list[0]:.2f} €/Go")
            if len(c_list) >= 2:
                p2.info(f"🥈 **{c_list[1]}**\n\n {v_list[1]:.2f} €/Go")
            if len(c_list) >= 3:
                p3.warning(f"🥉 **{c_list[2]}**\n\n {v_list[2]:.2f} €/Go")

        # --- SECTION 4 : L'AGENT IA (Analyseur de Données Avancé) ---
        st.markdown(
            "<br><div style='text-align: center;'><hr></div>",
            unsafe_allow_html=True
        )
        st.markdown("### 🤖 Assistant IA MyBestSim")
        st.markdown(
            "Posez une question sur vos données. L'IA analysera le catalogue et générera des réponses et des graphiques sur mesure."
        )

        # Initialisation de l'historique
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Interface de chat
        chat_container = st.container()

        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if "chart" in message:
                        st.plotly_chart(
                            message["chart"], use_container_width=True
                        )

        # Formulaire de question
        with st.form("ai_form", clear_on_submit=True):
            col_input, col_btn = st.columns([0.85, 0.15])

            user_question = col_input.text_input(
                "Votre question...",
                placeholder="Ex: Compare les 3 fournisseurs les plus rentables",
                label_visibility="collapsed"
            )
            submit_btn = col_btn.form_submit_button("Analyser")

        if submit_btn and user_question:
            with st.spinner("Analyse approfondie en cours..."):
                # 1. Préparation du contexte technique pour l'IA
                data_info = {
                    "columns": df_final.columns.tolist(),
                    "filtered_count": len(filtered_df),
                    "providers": filtered_df['fournisseur'].unique().tolist(),
                    "summary": filtered_df.describe().to_dict()
                }

                prompt = f"""
                Tu es un Expert Data Analyst chez MyBestSim.
                CONTEXTE:
                - Données disponibles: {data_info}
                - Le DataFrame 'filtered_df' contient les données filtrées par l'utilisateur.

                MISSION:
                Analyse la question : "{user_question}"

                CONSIGNES DE RÉPONSE:
                1. Analyse les données et fournis une réponse professionnelle et concise.
                2. Si une analyse quantitative est nécessaire, demande un graphique en utilisant ce format JSON à la fin de ta réponse :
                   {{ "chart": "type", "x": "colonne_x", "y": "colonne_y", "type_chart": "bar|pie|scatter|line" }}
                3. Types de graphiques : 'bar' (comparaison), 'pie' (répartition), 'scatter' (corrélation), 'line' (tendance).

                Réponds en français.
                """

                try:
                    response = model.generate_content(prompt)
                    full_text = response.text

                    # Extraction du JSON pour le graphique
                    chart_data = None
                    json_str = ""

                    if full_text and "{" in full_text and "}" in full_text:
                        try:
                            import re
                            match = re.search(r'\{.*\}', full_text, re.DOTALL)

                            if match:
                                json_str = match.group()
                                chart_data = json.loads(json_str)

                        except (json.JSONDecodeError, AttributeError, TypeError) as json_error:
                            st.warning(
                                f"Impossible d'extraire les paramètres du graphique : {json_error}"
                            )

                    # Ajout à l'historique
                    st.session_state.messages.append(
                        {"role": "user", "content": user_question}
                    )

                    # Construction de la réponse finale
                    final_content = full_text.replace(json_str, "").strip() if full_text else "L'IA n'a retourné aucun texte."

                    msg_entry = {
                        "role": "assistant",
                        "content": final_content
                    }

                    # Génération du graphique si demandé par l'IA
                    if chart_data:
                        try:
                            x_col = chart_data.get('x')
                            y_col = chart_data.get('y')
                            type_c = chart_data.get('type_chart')

                            if x_col in filtered_df.columns and y_col in filtered_df.columns:
                                if type_c == 'bar':
                                    fig = px.bar(
                                        filtered_df, x=x_col, y=y_col,
                                        color=x_col, text_auto='.2s'
                                    )
                                elif type_c == 'pie':
                                    fig = px.pie(
                                        filtered_df, names=x_col,
                                        values=y_col, hole=0.4
                                    )
                                elif type_c == 'scatter':
                                    fig = px.scatter(
                                        filtered_df, x=x_col, y=y_col,
                                        color='fournisseur'
                                    )
                                elif type_c == 'line':
                                    fig = px.line(
                                        filtered_df, x=x_col, y=y_col
                                    )
                                else:
                                    fig = None

                                if fig is not None:
                                    fig.update_layout(
                                        margin=dict(l=0, r=0, t=30, b=0),
                                        plot_bgcolor="rgba(0,0,0,0)"
                                    )
                                    msg_entry["chart"] = fig

                        except (ValueError, KeyError, TypeError) as chart_error:
                            st.warning(
                                f"Impossible de générer le graphique : {chart_error}"
                            )

                    st.session_state.messages.append(msg_entry)
                    st.rerun()

                except Exception as e:
                    st.error(f"Erreur IA : {e}")

except Exception as e:
    st.error(f"Une erreur critique est survenue : {e}")
