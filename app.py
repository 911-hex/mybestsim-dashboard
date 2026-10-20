from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------
# Configuration
# ----------------------------
st.set_page_config(
    page_title="MyBestSim | Dashboard eSIM",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "data"

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.6rem; padding-bottom: 2.5rem;}
      div[data-testid="stMetric"] {
        background: #f7f9fc;
        border: 1px solid #e5eaf2;
        padding: 16px 18px;
        border-radius: 12px;
      }
      div[data-testid="stMetricLabel"] {font-size: 0.92rem;}
      div[data-testid="stMetricValue"] {font-size: 1.8rem;}
      .subtitle {color: #667085; margin-top: -0.5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Load CSV files
# ----------------------------
@st.cache_data
def load_data(data_folder: str):
    folder = Path(data_folder)
    files = sorted(folder.glob("*.csv"))
    frames = []
    errors = []

    if not files:
        return pd.DataFrame(), [], ["Aucun fichier CSV trouvé dans le dossier data/."]

    for file in files:
        try:
            # sep=None helps detect commas or semicolons.
            df = pd.read_csv(file, sep=None, engine="python", encoding_errors="replace")
            df.columns = [str(c).strip().lower() for c in df.columns]

            required = {"price", "provider"}
            missing = required - set(df.columns)
            if missing:
                errors.append(f"{file.name} ignoré : colonne(s) manquante(s) {', '.join(sorted(missing))}.")
                continue

            # Add optional fields so files with slightly different schemas can be combined.
            for col in [
                "sku", "product_name", "country_code", "country_name", "data_gb",
                "data_display", "validity_days", "currency", "network", "top_up"
            ]:
                if col not in df.columns:
                    df[col] = pd.NA

            df["source_file"] = file.name
            frames.append(df)
        except Exception as exc:
            errors.append(f"{file.name} impossible à lire : {exc}")

    if not frames:
        return pd.DataFrame(), files, errors

    data = pd.concat(frames, ignore_index=True, sort=False)

    # Normalize text fields.
    for col in ["provider", "product_name", "country_name", "country_code", "currency", "network", "top_up"]:
        data[col] = data[col].astype("string").str.strip()

    # Normalize numeric fields (supports decimal commas in CSV values).
    for col in ["price", "data_gb", "validity_days"]:
        data[col] = (
            data[col].astype("string")
            .str.replace("\u00a0", "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        data[col] = pd.to_numeric(data[col], errors="coerce")

    # Keep only records with a valid price and provider for price statistics.
    data = data.dropna(subset=["price", "provider"])
    data = data[data["price"] >= 0].copy()
    data["provider"] = data["provider"].replace("", "Fournisseur inconnu").fillna("Fournisseur inconnu")
    data["country_name"] = data["country_name"].fillna("Pays non renseigné")
    data["product_name"] = data["product_name"].fillna("Produit sans nom")
    return data, files, errors


df, discovered_files, load_errors = load_data(str(DATA_DIR))

st.title("📶 MyBestSim — Dashboard eSIM")
st.markdown(
    '<p class="subtitle">Analyse des prix, des volumes de données et des fournisseurs à partir des fichiers CSV.</p>',
    unsafe_allow_html=True,
)

if load_errors:
    with st.expander("Messages de chargement", expanded=False):
        for message in load_errors:
            st.warning(message)

if df.empty:
    st.error("Aucune donnée exploitable. Ajoute tes fichiers CSV dans le dossier data/ puis actualise l'application.")
    st.stop()

# ----------------------------
# Sidebar filters
# ----------------------------
st.sidebar.header("Filtres")
providers = sorted(df["provider"].dropna().unique().tolist())
selected_providers = st.sidebar.multiselect(
    "Fournisseurs",
    options=providers,
    default=providers,
)
countries = sorted(df["country_name"].dropna().unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Pays / destinations",
    options=countries,
    default=[],
    help="Laisse vide pour inclure toutes les destinations.",
)

min_available = float(df["price"].min())
max_available = float(df["price"].max())
if min_available == max_available:
    price_range = (min_available, max_available)
else:
    price_range = st.sidebar.slider(
        "Fourchette de prix (€)",
        min_value=float(min_available),
        max_value=float(max_available),
        value=(float(min_available), float(max_available)),
    )

filtered = df[df["provider"].isin(selected_providers)].copy()
if selected_countries:
    filtered = filtered[filtered["country_name"].isin(selected_countries)]
filtered = filtered[filtered["price"].between(price_range[0], price_range[1])]

if filtered.empty:
    st.info("Aucun produit ne correspond aux filtres sélectionnés.")
    st.stop()

# ----------------------------
# Six required KPI indicators
# ----------------------------
total_products = len(filtered)
over_100 = int((filtered["price"] > 100).sum())
min_price = float(filtered["price"].min())
max_price = float(filtered["price"].max())
avg_price = float(filtered["price"].mean())

# Unlimited plans may have no numeric data_gb value; average only uses numeric values.
numeric_data = filtered["data_gb"].dropna()
avg_data = float(numeric_data.mean()) if not numeric_data.empty else None

st.subheader("Indicateurs clés")
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Nombre de produits", f"{total_products:,}".replace(",", " "))
k2.metric("Prix > 100 €", f"{over_100:,}".replace(",", " "))
k3.metric("Prix minimum", f"{min_price:.2f} €")
k4.metric("Prix maximum", f"{max_price:.2f} €")
k5.metric("Données moyennes", f"{avg_data:.2f} Go" if avg_data is not None else "N/D")
k6.metric("Prix moyen", f"{avg_price:.2f} €")

st.caption(
    "Note méthodologique : la moyenne de données (Go) est calculée uniquement sur les offres dont data_gb est numérique. "
    "Les offres illimitées sans valeur numérique sont exclues de cette moyenne, mais restent incluses dans les statistiques de prix."
)

# ----------------------------
# Charts
# ----------------------------
st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Nombre de produits par fournisseur")
    provider_counts = (
        filtered.groupby("provider", dropna=False)
        .size()
        .reset_index(name="Nombre de produits")
        .sort_values("Nombre de produits", ascending=False)
    )
    fig = px.bar(
        provider_counts,
        x="provider",
        y="Nombre de produits",
        color="provider",
        text="Nombre de produits",
        template="plotly_white",
    )
    fig.update_layout(showlegend=False, xaxis_title="Fournisseur", yaxis_title="Produits")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Prix moyen par fournisseur")
    provider_prices = (
        filtered.groupby("provider", as_index=False)["price"]
        .mean()
        .rename(columns={"price": "Prix moyen (€)"})
        .sort_values("Prix moyen (€)", ascending=False)
    )
    fig = px.bar(
        provider_prices,
        x="provider",
        y="Prix moyen (€)",
        color="provider",
        text_auto=".2f",
        template="plotly_white",
    )
    fig.update_layout(showlegend=False, xaxis_title="Fournisseur", yaxis_title="Prix moyen (€)")
    st.plotly_chart(fig, use_container_width=True)

left2, right2 = st.columns(2)
with left2:
    st.subheader("Répartition des prix")
    fig = px.histogram(
        filtered,
        x="price",
        nbins=30,
        labels={"price": "Prix (€)"},
        template="plotly_white",
    )
    fig.update_layout(yaxis_title="Nombre de produits", xaxis_title="Prix (€)")
    st.plotly_chart(fig, use_container_width=True)

with right2:
    st.subheader("Offres par destination")
    country_counts = (
        filtered.groupby("country_name")
        .size()
        .reset_index(name="Nombre de produits")
        .sort_values("Nombre de produits", ascending=False)
        .head(15)
    )
    fig = px.bar(
        country_counts.sort_values("Nombre de produits"),
        x="Nombre de produits",
        y="country_name",
        orientation="h",
        labels={"country_name": "Destination"},
        template="plotly_white",
    )
    fig.update_layout(xaxis_title="Nombre de produits", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# Data table and download
# ----------------------------
st.divider()
st.subheader("Explorer les produits")
search = st.text_input("Rechercher par nom, fournisseur ou destination", placeholder="Ex. Espagne, Airalo, 10 Go")
table = filtered.copy()
if search.strip():
    term = search.strip().casefold()
    mask = (
        table["product_name"].astype(str).str.casefold().str.contains(term, na=False)
        | table["provider"].astype(str).str.casefold().str.contains(term, na=False)
        | table["country_name"].astype(str).str.casefold().str.contains(term, na=False)
    )
    table = table[mask]

display_cols = [
    "provider", "product_name", "country_name", "data_display", "data_gb",
    "validity_days", "price", "currency", "network", "top_up", "source_file"
]
display_cols = [c for c in display_cols if c in table.columns]
renames = {
    "provider": "Fournisseur",
    "product_name": "Produit",
    "country_name": "Destination",
    "data_display": "Données affichées",
    "data_gb": "Données (Go)",
    "validity_days": "Validité (jours)",
    "price": "Prix",
    "currency": "Devise",
    "network": "Réseau",
    "top_up": "Recharge possible",
    "source_file": "Fichier source",
}
st.dataframe(
    table[display_cols].rename(columns=renames),
    use_container_width=True,
    hide_index=True,
)

csv_bytes = table[display_cols].to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "⬇️ Télécharger les données filtrées (CSV)",
    data=csv_bytes,
    file_name="mybestsim_donnees_filtrees.csv",
    mime="text/csv",
)

st.caption(
    f"{len(filtered):,} produits affichés après filtres · "
    f"{len(discovered_files)} fichier(s) CSV détecté(s) dans data/".replace(",", " ")
)
