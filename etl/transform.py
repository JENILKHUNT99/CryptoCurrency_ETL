import pandas as pd
from datetime import datetime
from etl.logger import get_logger
from config.coins import COIN_CATEGORIES

logger = get_logger(__name__)

def transform_data(data, run_date):
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
    dim_category["category_id"] = dim_category.index + 1
    dim_category = dim_category.rename(columns={"category": "category_name"})
    dim_category = dim_category[["category_id", "category_name"]]

    # Map category_id back to df
    df = df.merge(
        dim_category.rename(columns={"category_name": "category"}),
        on="category", how="left"
    )

    # ─── dim_coin ───
    dim_coin = (
        df[["symbol", "name", "category_id"]]
        .drop_duplicates()
        .rename(columns={"symbol": "coin_symbol", "name": "coin_name"})
        .reset_index(drop=True)
    )
    dim_coin["coin_id"] = dim_coin.index + 1
    dim_coin = dim_coin[["coin_id", "coin_symbol", "coin_name", "category_id"]]

    # Map coin_id back to df — THIS fixes your coin_id problem! 😄
    df = df.merge(
        dim_coin[["coin_id", "coin_symbol"]].rename(columns={"coin_symbol": "symbol"}),
        on="symbol", how="left"
    )

    # ─── dim_date ───
    # Your brilliant idea — TWO dates! ✅
    etl_run_dt = pd.to_datetime(run_date)
    
    # Collect all unique dates — ETL run date + all API last_updated dates
    api_dates = pd.to_datetime(df["last_updated"]).dt.floor("h")
    all_dates = pd.concat([
        pd.Series([etl_run_dt]),
        api_dates
    ]).drop_duplicates().reset_index(drop=True)

    dim_date_rows = []
    for dt in all_dates:
        dim_date_rows.append({
            "full_date": dt.date(),
            "hour": dt.hour,
            "day": dt.day,
            "day_name": dt.strftime("%A"),
            "month": dt.month,
            "month_name": dt.strftime("%B"),
            "quarter": f"Q{(dt.month - 1) // 3 + 1}",
            "year": dt.year,
            "is_weekend": dt.weekday() >= 5
        })

    dim_date = pd.DataFrame(dim_date_rows).drop_duplicates().reset_index(drop=True)
    dim_date["date_id"] = dim_date.index + 1
    dim_date = dim_date[[
        "date_id", "full_date", "hour", "day", "day_name",
        "month", "month_name", "quarter", "year", "is_weekend"
    ]]

    # ─── dim_currency ───
    dim_currency = pd.DataFrame([{
        "currency_name": "US Dollar",
        "currency_symbol": "usd"
    }])
    dim_currency["currency_id"] = 1
    dim_currency = dim_currency[["currency_id", "currency_name", "currency_symbol"]]

    # ─── fact_crypto_prices ───
    # Get ETL run date_id and API last_updated date_id
    etl_date_id = dim_date[
        (dim_date["full_date"] == etl_run_dt.date()) &
        (dim_date["hour"] == etl_run_dt.hour)
    ]["date_id"].iloc[0]

    df["api_dt"] = pd.to_datetime(df["last_updated"]).dt.floor("h")

    # Map api date_id
    date_map = dim_date.copy()
    date_map["dt_key"] = pd.to_datetime(
        date_map["full_date"].astype(str)
    ) + pd.to_timedelta(date_map["hour"], unit="h")

    df["api_date_id"] = df["api_dt"].map(
        date_map.set_index("dt_key")["date_id"]
    )

    fact_crypto_prices = pd.DataFrame({
        "coin_id": df["coin_id"],
        "etl_run_date_id": etl_date_id,
        "api_updated_date_id": df["api_date_id"],
        "currency_id": 1,
        "price": df["current_price"],
        "market_cap": df["market_cap"],
        "volume": df["total_volume"],
        "high_24h": df["high_24h"],
        "low_24h": df["low_24h"],
        "price_change_percent": df["price_change_percentage_24h"]
    }).reset_index(drop=True)

    fact_crypto_prices["price_id"] = fact_crypto_prices.index + 1
    fact_crypto_prices = fact_crypto_prices[[
        "price_id", "coin_id", "etl_run_date_id", "api_updated_date_id",
        "currency_id", "price", "market_cap", "volume",
        "high_24h", "low_24h", "price_change_percent"
    ]]

    logger.info(f"Transform complete! Coins: {len(dim_coin)}, Categories: {len(dim_category)}, Dates: {len(dim_date)}")
    return dim_category, dim_coin, dim_date, dim_currency, fact_crypto_prices