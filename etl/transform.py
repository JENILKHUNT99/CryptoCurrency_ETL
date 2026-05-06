import pandas as pd # type: ignore
from etl.logger import get_logger
from config.coins import COIN_CATEGORIES, CATEGORY_ID

logger = get_logger(__name__)

def transform_data(data, run_date=None):
    logger.info("Transforming data...")

    df = pd.DataFrame(data)

    if df.empty:
        logger.warning("No data received for transform!")
        return None, None, None, None, None

    # Add category
    df["category"] = df["id"].map(COIN_CATEGORIES).fillna("Other")

    # ─── dim_category ───
    dim_category = (
        df[["category"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_category["category_id"] = dim_category["category"].map(CATEGORY_ID).fillna(99).astype(int)
    dim_category = dim_category.rename(columns={"category": "category_name"})
    dim_category = dim_category[["category_id", "category_name"]]

    # Map category_id back to df
    df = df.merge(
        dim_category.rename(columns={"category_name": "category"}),
        on="category", how="left"
    )
    df.drop(columns=["category"], inplace=True)

    # ─── dim_coin ───
    dim_coin = (
        df[["id","symbol", "name", "category_id"]]
        .drop_duplicates()
        .rename(columns={"id": "coin_id", "symbol": "coin_symbol", "name": "coin_name"})
        .reset_index(drop=True)
    )
    dim_coin = dim_coin[["coin_id", "coin_symbol", "coin_name", "category_id"]]


    # ─── dim_date ───  
    etl_run_dt = pd.to_datetime(run_date) if run_date else pd.Timestamp.now(tz="UTC")
    
    # Collect all unique dates — ETL run date + all API last_updated dates
    api_dt = pd.to_datetime(df["last_updated"],errors="coerce").dt.round("h")
    all_dates = pd.concat([
        pd.Series([etl_run_dt.round("h")]),
        api_dt
    ]).dropna().drop_duplicates().reset_index(drop=True)

    dim_date = pd.DataFrame({
        "datetime": all_dates
    })
    dim_date["date_id"] = dim_date["datetime"].dt.strftime("%Y%m%d%H").astype(int)
    dim_date["full_date"] = dim_date["datetime"].dt.date
    dim_date["hour"] = dim_date["datetime"].dt.hour
    dim_date["day"] = dim_date["datetime"].dt.day
    dim_date["month"] = dim_date["datetime"].dt.month
    dim_date["quarter"] = dim_date["datetime"].dt.quarter
    dim_date["year"] = dim_date["datetime"].dt.year
    dim_date["day_name"] = dim_date["datetime"].dt.day_name()
    dim_date["month_name"] = dim_date["datetime"].dt.month_name()
    dim_date["is_weekend"] = dim_date["datetime"].dt.weekday >= 5  
    dim_date = dim_date[[
        "date_id", "datetime","full_date", "hour", "day", "day_name",
        "month", "month_name", "quarter", "year", "is_weekend"
    ]]

    # ─── dim_currency ───
    dim_currency = pd.DataFrame([{
        "currency_id": 1,
        "currency_name": "US Dollar",
        "currency_symbol": "usd"
    }])


    # ─── fact_crypto_prices ───
    api_date_id = api_dt.dt.strftime("%Y%m%d%H").fillna(0000000000).astype(int)
    etl_date_id = int(etl_run_dt.round("h").strftime("%Y%m%d%H"))

    fact_crypto_prices = pd.DataFrame({
        "price_id": df["id"].astype(str).fillna("unknown") + "_" + api_dt.dt.strftime("%Y%m%d%H").fillna("0000000000"), 
        "coin_id": df["id"],
        "etl_run_date_id": etl_date_id,
        "api_updated_date_id": api_date_id,
        "currency_id": 1,  # USD
        "price": df["current_price"],
        "market_cap": df["market_cap"],
        "volume": df["total_volume"],
        "high_24h": df["high_24h"],
        "low_24h": df["low_24h"],
        "price_change_percent": df["price_change_percentage_24h"]
    }).dropna(subset=["coin_id", "price"])
        
    
    logger.info(f"Transform complete! Coins: {len(dim_coin)}, Categories: {len(dim_category)}, Dates: {len(dim_date)}")
    return dim_category, dim_coin, dim_date, dim_currency, fact_crypto_prices