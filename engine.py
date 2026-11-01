from datetime import datetime
import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, expected_returns, risk_models
from sqlalchemy import text
import yfinance as yf


class Stock:

    def __init__(self, ticker_symbol: str):
        self.ticker_symbol = ticker_symbol.upper()
        self._yf_ticker = yf.Ticker(self.ticker_symbol)

    def get_latest_price(self) -> float | None:
        try:
            data = self._yf_ticker.history(period="1d")
            if not data.empty:
                return round(float(data["Close"].iloc[-1]), 2)
        except Exception as e:
            print(f"error loading {self.ticker_symbol} : {e}")
            return None


class Portfolio:

    def __init__(self, streamlit_connection):
        self.conn = streamlit_connection
        self._create_table()
        self._create_table_stock_series()

    def _create_table(self):
        try:
            with self.conn.engine.begin() as connection:
                connection.execute(
                    text("""CREATE TABLE IF NOT EXISTS asset_prices(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_name TEXT,
                    ticker TEXT, 
                    shares REAL,
                    unit_price REAL, 
                    total_value REAL,
                    timestamp TEXT
                );""")
                )
        except Exception as e:
            print(f"Error creating database table {e}")

    def _create_table_stock_series(self):
        try:
            with self.conn.engine.begin() as connection:
                connection.execute(
                    text("""CREATE TABLE IF NOT EXISTS stock_series(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock TEXT, date TEXT, open REAL, high REAL, low REAL, 
                    close REAL, adj_close REAL, volume INTEGER, timestamp TEXT
                );""")
                )
        except Exception as e:
            print(f"Error creating database stock series {e}")

    def add_asset_price(self, stock: Stock, price: float):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn.session as session:
            session.execute(
                text(
                    """INSERT INTO asset_prices (ticker, shares, unit_price, total_value, timestamp) 
                       VALUES(:ticker, :shares, :unit_price, :total_value, :timestamp)"""
                ),
                {
                    "ticker": stock.ticker_symbol,
                    "shares": 1.0,
                    "unit_price": price,
                    "total_value": price,
                    "timestamp": current_time,
                },
            )
            session.commit()

    def add_stock_series(
            self,
            stock: str,
            date: str,
            open: float,
            high: float,
            low: float,
            close: float,
            adj_close: float,
            volume: int,
    ):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn.session as session:
            session.execute(
                text(
                    """INSERT INTO stock_series (stock, date, open, high, low, close, adj_close, volume, timestamp) 
                       VALUES(:stock, :date, :open, :high, :low, :close, :adj_close, :volume, :timestamp)"""
                ),
                {
                    "stock": stock,
                    "date": date,
                    "open": open,
                    "high": high,
                    "low": low,
                    "close": close,
                    "adj_close": adj_close,
                    "volume": volume,
                    "timestamp": current_time,
                },
            )
            session.commit()

    def get_history(self):
        return self.conn.query("SELECT * from asset_prices", ttl=0)

    def get_stock_series(self, symbol, start, end, interval):
        df = yf.download(symbol, start, end, interval)
        return df

    def calculate_risk_metrics(self, df: pd.DataFrame):
        if df.empty or "Close" not in df.columns:
            return None
        close_data = df["Close"]

        if isinstance(close_data, pd.DataFrame):
            close_data = close_data.iloc[:, 0]

        # Dataframe met returns
        returns = close_data.pct_change().dropna()
        if len(returns) < 2:
            return None

        # Totale rendement
        total_return = (close_data.iloc[-1] / close_data.iloc[0]) - 1

        # Jaarlijkse volatiliteit (gecorrigeerd)
        daily_vol = returns.std()
        ann_vol = daily_vol * np.sqrt(252)

        # Maximum drawdown (gecorrigeerd)
        cumulative_max = close_data.cummax()
        drawdown = (close_data - cumulative_max) / cumulative_max
        max_drawdown = drawdown.min()

        # Sharpe ratio
        annual_return = returns.mean() * 252
        sharpe_ratio = ((annual_return - 0.03) / ann_vol) if ann_vol > 0 else 0

        return {
            "Total Return": total_return,
            "Annual Volatility": ann_vol,
            "Max Drawdown": max_drawdown,
            "Sharpe Ratio": sharpe_ratio,
        }

    def save_portfolio_snapshot(self, holdings: dict, portfolio_name: str="default_portfolio"):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.conn.session as session:
            with session.begin():
                for ticker, position in holdings.items():
                    stock = Stock(ticker)
                    price = stock.get_latest_price()

                    if price is not None:
                        total_value = price * position
                        session.execute(
                            text(
                                """INSERT INTO asset_prices 
                                   (portfolio_name, ticker, shares, unit_price, total_value, timestamp) 
                                   VALUES (:portfolio_name, :ticker, :shares, :unit_price, :total_value, :timestamp)"""
                            ),
                            {
                                "portfolio_name":portfolio_name,
                                "ticker": ticker,
                                "shares": position,
                                "unit_price": price,
                                "total_value": total_value,
                                "timestamp": current_time,
                            },
                        )

    def optimize_portfolio(self, tickers, start, end):
        try:
            close_data = {}
            for ticker in tickers:
                # Download per aandeel apart om multi-index en versieproblemen te voorkomen
                df_t = yf.download(ticker, start=start, end=end, progress=False)
                if not df_t.empty and "Close" in df_t.columns:
                    s = df_t["Close"]
                    # Zorg dat het altijd een schone Series is
                    if isinstance(s, pd.DataFrame):
                        s = s.iloc[:, 0]
                    close_data[ticker] = s

            # Samenvoegen tot één DataFrame en ontbrekende dagen weglaten
            data = pd.DataFrame(close_data).dropna()

            if data.empty or data.shape[1] < 2:
                return None, None

            mu = expected_returns.mean_historical_return(data)
            S = risk_models.sample_cov(data)

            ef = EfficientFrontier(mu, S)
            ef.max_sharpe(risk_free_rate=0.03)
            cleaned_weights = ef.clean_weights()
            performance = ef.portfolio_performance(risk_free_rate=0.03)

            return cleaned_weights, performance
        except Exception as e:
            print(f"Fout bij portfolio optimalisatie: {e}")
            return None, None