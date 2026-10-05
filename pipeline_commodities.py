import sqlite3
import numpy as np
import pandas as pd
import yfinance as yf

# ==========================================
# STEP 1: DOWNLOAD DATI DI MERCATO
# ==========================================
tickers = {
    "Wheat": "ZW=F",  # Trigo / Grano
    "Soybean": "ZS=F",  # Soja
    "Corn": "ZC=F",  # Maíz / Mais
    "Crude_Oil": "CL=F",  # Petróleo / Petrolio
    "Natural_Gas": "NG=F",  # Gas Natural
}

print("1/3 Download dati storici in corso...")
frames = []

for name, symbol in tickers.items():
    print(f"   -> Scaricamento: {name} ({symbol})...")
    df = yf.download(symbol, start="2023-01-01", progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        close_series = df["Close"].iloc[:, 0]
    else:
        close_series = df["Close"]

    temp = pd.DataFrame(
        {
            "Date": df.index,
            "Commodity": name,
            "Price": close_series.values,
        }
    ).dropna()

    frames.append(temp)

all_data = pd.concat(frames, ignore_index=True)
all_data["Date"] = pd.to_datetime(all_data["Date"]).dt.date

# ==========================================
# STEP 2: METRICHE QUANTITATIVE E ANOMALIE
# ==========================================
print("\n2/3 Calcolo indicatori statistici e rilevamento shock...")

processed_list = []

# Iteriamo su ciascuna commodity per evitare problemi di indice
for commodity_name, group in all_data.groupby("Commodity"):
    df_comm = group.sort_values("Date").copy()

    # 1. Rendimento logaritmico
    df_comm["Log_Return"] = np.log(df_comm["Price"] / df_comm["Price"].shift(1))

    # 2. Medie mobili
    df_comm["SMA_30"] = (
        df_comm["Price"].rolling(window=30, min_periods=10).mean()
    )
    df_comm["SMA_90"] = (
        df_comm["Price"].rolling(window=90, min_periods=30).mean()
    )

    # 3. Volatilità rolling annualizzata (252 giorni di trading)
    rolling_std = df_comm["Log_Return"].rolling(window=30, min_periods=10).std()
    rolling_mean = (
        df_comm["Log_Return"].rolling(window=30, min_periods=10).mean()
    )
    df_comm["Rolling_Vol_Annualized"] = rolling_std * np.sqrt(252)

    # 4. Z-Score
    df_comm["Z_Score"] = (df_comm["Log_Return"] - rolling_mean) / rolling_std

    # 5. Rilevamento shock
    df_comm["Anomaly_Flag"] = 0
    df_comm.loc[df_comm["Z_Score"].abs() >= 2.5, "Anomaly_Flag"] = 1

    df_comm["Anomaly_Type"] = "Normal"
    df_comm.loc[df_comm["Z_Score"] >= 2.5, "Anomaly_Type"] = "Price Spike"
    df_comm.loc[df_comm["Z_Score"] <= -2.5, "Anomaly_Type"] = "Sharp Drop"

    processed_list.append(df_comm)

enriched_df = pd.concat(processed_list, ignore_index=True)

# Arrotondamenti
enriched_df = enriched_df.round(
    {
        "Price": 2,
        "Log_Return": 4,
        "SMA_30": 2,
        "SMA_90": 2,
        "Rolling_Vol_Annualized": 4,
        "Z_Score": 2,
    }
)

total_anomalies = int(enriched_df["Anomaly_Flag"].sum())
print(f"   -> Record totali elaborati: {len(enriched_df)}")
print(f"   -> Shock identificati (|Z| >= 2.5): {total_anomalies}")

# ==========================================
# STEP 3: DATABASE SQLITE & VISTE ANALITICHE
# ==========================================
print("\n3/3 Creazione database SQLite e viste SQL analitiche...")
db_file = "market_intelligence.db"
conn = sqlite3.connect(db_file)

# 1. Scrittura tabella principale
enriched_df.to_sql(
    "fact_commodity_prices", conn, if_exists="replace", index=False
)

# 2. Vista analitica mensile
cursor = conn.cursor()
cursor.execute("DROP VIEW IF EXISTS view_monthly_cost_summary;")
cursor.execute(
    """
CREATE VIEW view_monthly_cost_summary AS
SELECT 
    Commodity,
    strftime('%Y-%m', Date) AS Month_Year,
    ROUND(AVG(Price), 2) AS Avg_Monthly_Price,
    ROUND(MIN(Price), 2) AS Min_Price,
    ROUND(MAX(Price), 2) AS Max_Price,
    ROUND(AVG(Rolling_Vol_Annualized) * 100, 2) AS Avg_Annualized_Vol_Pct,
    SUM(Anomaly_Flag) AS Shock_Count
FROM fact_commodity_prices
GROUP BY Commodity, Month_Year
ORDER BY Commodity ASC, Month_Year DESC;
"""
)

# 3. Vista analitica per allerte
cursor.execute("DROP VIEW IF EXISTS view_active_alerts;")
cursor.execute(
    """
CREATE VIEW view_active_alerts AS
SELECT 
    Date,
    Commodity,
    Price,
    ROUND(Log_Return * 100, 2) AS Daily_Change_Pct,
    Z_Score,
    Anomaly_Type
FROM fact_commodity_prices
WHERE Anomaly_Flag = 1
ORDER BY Date DESC;
"""
)
conn.commit()

# Esportazione CSV per caricamento immediato in Power BI
enriched_df.to_csv("commodity_intelligence_feed.csv", index=False)

print("\n--- Pipeline completata senza errori! ---")
print(f"File generati:")
print(f"  • Database SQL: {db_file}")
print(f"  • File per la dashboard: commodity_intelligence_feed.csv")

# Test di lettura dalla vista SQL appena creata
alerts_sample = pd.read_sql_query(
    "SELECT * FROM view_active_alerts LIMIT 5;", conn
)
print("\nPrime 5 allerte estratte direttamente con SQL:")
print(alerts_sample.to_string(index=False))

conn.close()