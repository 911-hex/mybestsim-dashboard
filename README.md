# MyBestSim — eSIM Dashboard

**Explore, compare and analyse eSIM offers from multiple providers.**

MyBestSim Dashboard is a Streamlit application designed to make eSIM market data easier to explore. It brings together offers from different providers in one place, with interactive filters, pricing insights and downloadable results.

## Features

- **Market overview** — Track product counts, minimum and maximum prices, average prices and available data volumes.
- **Provider comparison** — Compare the number of offers and average prices across providers.
- **Price analysis** — Explore price distributions and identify the destinations most represented in the dataset.
- **Flexible filters** — Narrow results by provider, destination and price range.
- **Product search** — Find specific offers in the available data.
- **Data export** — Download filtered results for further analysis.

## Project structure

```text
mybestsim-dashboard/
├── app.py
├── requirements.txt
├── README.md
└── data/
    ├── 4sesim.csv
    ├── airalo.csv
    ├── alosim.csv
    └── esimx.csv
```

The dashboard automatically loads CSV files from the `data/` directory. Additional datasets can be added to the same folder, provided they contain the required fields.

## Getting started

### Requirements

- Python 3
- pip

### 1. Clone the repository

```bash
git clone https://github.com/TON-PSEUDO/mybestsim-dashboard.git
cd mybestsim-dashboard
```

Replace `TON-PSEUDO` with the appropriate GitHub username and repository URL.

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the dashboard

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal, usually `http://localhost:8501`.

To stop the application, press `Ctrl + C` in the terminal.

## Data format

CSV files are read from the `data/` directory. The dashboard supports additional columns, while the following fields are used for its main functionality:

| Field | Purpose |
|---|---|
| `provider` | eSIM provider |
| `price` | Offer price |
| `data_gb` | Data allowance in GB, when available |
| `product_name` | Offer name, when available |
| `country_name` | Destination, when available |

The `provider` and `price` fields are required. Other fields are used where available.

**Data privacy:** Before committing CSV files to a public repository, make sure the datasets are permitted to be shared publicly.

## Deploying the dashboard

The application can be deployed using [Streamlit Community Cloud](https://share.streamlit.io/).

1. Sign in with GitHub.
2. Create a new app.
3. Select the repository and the `main` branch.
4. Set `app.py` as the application entry point.
5. Deploy and test the public URL.

The repository must include the required data files, or the application must be configured to retrieve them from another accessible source.

## Metrics and calculations

- **Products above €100:** includes offers priced strictly above €100.
- **Minimum, maximum and average price:** calculated from valid numeric prices.
- **Average data allowance:** calculated from numeric `data_gb` values. Unlimited plans without a numeric allowance are excluded.
- **Filtered results:** filters apply to the displayed metrics, charts, table and exported data.

## Troubleshooting

- **Streamlit command not found:** activate the virtual environment and reinstall the dependencies if needed.
- **CSV file not loaded:** check that the file is in `data/` and includes `provider` and `price`.
- **Column names differ:** update the column mapping in `app.py` to match the dataset.

## About

MyBestSim Dashboard is a data exploration project focused on making eSIM offers easier to compare through a clear, interactive interface.

Built with Python, Pandas, Plotly and Streamlit.
