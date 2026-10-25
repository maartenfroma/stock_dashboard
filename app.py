from datetime import date, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from groq import Groq

from engine import Portfolio, Stock

# --- 1. PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Portfolio & Risk Dashboard", page_icon="📈", layout="wide"
)

# Custom CSS voor een professionele fintech uitstraling en optimale leesbaarheid
st.markdown(
    """
    <style>
    /* Algemene achtergrond en standaard tekst */
    .stApp {
        background-color: #0b0e14;
        color: #e6edf3;
    }
    
    /* Hoofd 'kaarten' voor secties */
    .fintech-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 24px;
        border-radius: 14px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4);
        margin-bottom: 24px;
    }
    
    /* Subtiele accentkleur voor titels binnen kaarten */
    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #58a6ff;
        margin-bottom: 16px;
    }
    
    /* --- VERBETERDE LEESBAARHEID METRICS --- */
    [data-testid="stMetricValue"] {
        color: #58a6ff !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-weight: 500 !important;
    }
    
    /* --- INVOERVELDEN & SELECTBOXEN --- */
    .stTextInput input, .stNumberInput input {
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    
    /* Selectbox dropdown container */
    div[data-baseweb="select"] > div {
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    
    /* --- KOPPEN STRAKKER MAKEN --- */
    .stButton>button {
        background-color: #238636;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #2ea043;
        border-color: #3fb950;
        color: white;
    }
    
    /* --- SIDEBAR VERBETERDE LEESBAARHEID --- */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #30363d;
    }
    [data-testid="stSidebar"] .stRadio label, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] div {
        color: #e6edf3 !important;
    }
    
    /* --- EXPANDER & TABELLEN --- */
    .streamlit-expanderHeader {
        background-color: #1b222d;
        border-radius: 8px;
        border: 1px solid #30363d;
        color: #e6edf3 !important;
    }
    .streamlit-expanderContent {
        background-color: #161b22 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d;
        border-top: none;
        border-radius: 0 0 8px 8px;
    }
    
    /* Dataframe / Tabelaanpassing */
    [data-testid="stDataFrame"] {
        background-color: #0d1117 !important;
        border-radius: 8px;
        border: 1px solid #30363d;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown("### 📊 Pro Portfolio & Investment Dashboard")

conn = st.connection("sql")
my_portfolio = Portfolio(conn)

st.sidebar.header("⚙️ Home")
st.sidebar.markdown("---")

menu_choice = st.sidebar.radio(
    "Navigation",
    [
        "📊 Portfolio Management",
        "Risk & Historical Analysis",
        "Database Commitment",
        "AI Portfolio Analyst",
    ],
)
st.sidebar.markdown("---")
st.sidebar.info("Navigate options.")

if menu_choice == "Risk & Historical Analysis":
    st.subheader("Risk & Historical Analysis YFinance")

    col1, col2, col3 = st.columns(3)
    col_start_date, col_end_date = st.columns(2)

    with col1:
        symbol = st.text_input("Symbol", value="AAPL").upper()
    with col2:
        interval = st.selectbox("Interval", options=["1d", "1wk", "1mo"], index=0)
    with col3:
        st.write("")
    with col_start_date:
        start_date = st.date_input(
            "Start date", value=date.today() - timedelta(days=365)
        )
    with col_end_date:
        end_date = st.date_input("End date", value=date.today())

    if st.button("Download"):
        data = my_portfolio.get_stock_series(
            symbol=symbol,
            start=str(start_date),
            end=str(end_date),
            interval=interval,
        )

        if not data.empty:
            st.success(f"Analysis ready for {symbol}")

            risk_metrics = my_portfolio.calculate_risk_metrics(data)
            if risk_metrics and isinstance(risk_metrics, dict):
                st.markdown('<div class="fintech-card">', unsafe_allow_html=True)
                st.markdown(
                    '<div class="card-title">📊 Risk and Return Metrics</div>',
                    unsafe_allow_html=True,
                )
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric(
                        label="Total Return",
                        value=f"{risk_metrics['Total Return']*100:.2f}%",
                    )
                with m2:
                    st.metric(
                        label="Annual Volatility",
                        value=f"{risk_metrics['Annual Volatility']*100:.2f}%",
                    )
                with m3:
                    st.metric(
                        label="Max Drawdown",
                        value=f"{risk_metrics['Max Drawdown']*100:.2f}%",
                    )
                with m4:
                    st.metric(
                        label="Sharpe Ratio", value=f"{risk_metrics['Sharpe Ratio']:.2f}"
                    )
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="fintech-card">', unsafe_allow_html=True)
            st.markdown(
                f'<div class="card-title">📈 Historical price series {symbol}</div>',
                unsafe_allow_html=True,
            )

            fig_series, ax_series = plt.subplots(figsize=(10, 4))
            fig_series.patch.set_facecolor("#161b22")
            ax_series.set_facecolor("#161b22")

            close_data = data["Close"]
            if isinstance(close_data, pd.DataFrame):
                close_data = close_data.iloc[:, 0]

            ax_series.plot(
                data.index,
                close_data,
                linestyle="-",
                color="#3fb950",
                linewidth=2,
            )
            ax_series.tick_params(colors="#e6edf3")
            ax_series.xaxis.label.set_color("#e6edf3")
            ax_series.yaxis.label.set_color("#e6edf3")
            ax_series.grid(True, linestyle="--", alpha=0.2)

            for spine in ax_series.spines.values():
                spine.set_color("#30363d")

            plt.xticks(rotation=45)
            fig_series.tight_layout()
            st.pyplot(fig_series)

            with st.expander("Show historical data"):
                st.dataframe(data, width="stretch")

            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("No data input found")

elif menu_choice == "📊 Portfolio Management":
    st.subheader("💼 Your personal portfolio composition")

    # 1. Beheer kaarten
    st.markdown('<div class="fintech-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-title">1. Select your stocks & position</div>',
        unsafe_allow_html=True,
    )

    if "portfolio_holdings" not in st.session_state:
        st.session_state.portfolio_holdings = {
            "AAPL": 10,
            "MSFT": 5,
            "GOOGL": 8,
        }

    col_add_t, col_add_q, col_add_btn = st.columns([2, 1, 1])

    with col_add_t:
        new_ticker = st.text_input("Ticker Symbol", value="NVDA").upper()
    with col_add_q:
        new_shares = st.number_input("Position n", min_value=1, value=10, step=1)
    with col_add_btn:
        st.write("")
        st.write("")
        if st.button("Add to portfolio"):
            if new_ticker:
                st.session_state.portfolio_holdings[new_ticker] = new_shares
                st.success(f"Added: {new_shares}x {new_ticker} to portfolio!")

    st.markdown("</div>", unsafe_allow_html=True)

    # 2. Waarde & Allocatie
    if st.session_state.portfolio_holdings:
        st.markdown('<div class="fintech-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="card-title">2. Actual Portfolio Value &'
            " Distribution</div>",
            unsafe_allow_html=True,
        )

        portfolio_data = []
        total_portfolio_value = 0.0

        for ticker, shares in st.session_state.portfolio_holdings.items():
            stock_obj = Stock(ticker)
            latest_price = stock_obj.get_latest_price()

            if latest_price is not None:
                position_value = latest_price * shares
                total_portfolio_value += position_value
                portfolio_data.append({
                    "Ticker": ticker,
                    "Position shares": shares,
                    "Actual Price ($)": latest_price,
                    "Position Value ($)": position_value,
                })
            else:
                portfolio_data.append({
                    "Ticker": ticker,
                    "Position shares": shares,
                    "Actual Price ($)": 0.0,
                    "Position Value ($)": 0.0,
                })

        df_portfolio = pd.DataFrame(portfolio_data)

        if total_portfolio_value > 0:
            df_portfolio["Weight (%)"] = (
                                                 df_portfolio["Position Value ($)"] / total_portfolio_value
                                         ) * 100
        else:
            df_portfolio["Weight (%)"] = 0.0

        st.metric(
            label="Total Portfolio Value",
            value=f"${total_portfolio_value:,.2f}",
        )

        st.dataframe(
            df_portfolio.style.format({
                "Actual Price ($)": "${:,.2f}",
                "Position Value ($)": "${:,.2f}",
                "Weight (%)": "{:.1f}%",
            }),
            width="stretch",
        )

        st.markdown("---")
        col_del_t, col_del_btn = st.columns([2, 1])
        with col_del_t:
            ticker_to_remove = st.selectbox(
                "Remove stock",
                options=list(st.session_state.portfolio_holdings.keys()),
            )
        with col_del_btn:
            st.write("")
            st.write("")
            if st.button("Remove selection"):
                if ticker_to_remove in st.session_state.portfolio_holdings:
                    del st.session_state.portfolio_holdings[ticker_to_remove]
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # 3. GEAVANCEERDE RISICO-OPTIMALISATIE (PYPORTFOLIOPOT)
        st.markdown('<div class="fintech-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="card-title">🚀 Advanced Portfolio Optimization (Max'
            " Sharpe)</div>",
            unsafe_allow_html=True,
        )
        st.write(
            "Bereken automatisch de ideale gewichten voor je gekozen aandelen op"
            " basis van historische data."
        )

        if st.button("Optimize Portfolio Weights"):
            tickers_list = list(st.session_state.portfolio_holdings.keys())
            if len(tickers_list) > 1:
                start_opt = str(date.today() - timedelta(days=365))
                end_opt = str(date.today())

                opt_weights, perf = my_portfolio.optimize_portfolio(
                    tickers_list, start_opt, end_opt
                )

                if opt_weights and perf:
                    exp_return, volatility, sharpe = perf

                    op1, op2, op3 = st.columns(3)
                    with op1:
                        st.metric(
                            label="Expected Annual Return",
                            value=f"{exp_return*100:.2f}%",
                        )
                    with op2:
                        st.metric(label="Optimal Volatility", value=f"{volatility*100:.2f}%")
                    with op3:
                        st.metric(label="Optimized Sharpe Ratio", value=f"{sharpe:.2f}")

                    st.markdown("#### 💡 Recommended Optimal Weights:")
                    df_weights = pd.DataFrame(
                        list(opt_weights.items()),
                        columns=["Ticker", "Recommended Weight"],
                    )
                    df_weights["Recommended Weight (%)"] = (
                            df_weights["Recommended Weight"] * 100
                    )
                    st.dataframe(
                        df_weights[["Ticker", "Recommended Weight (%)"]].style.format({
                            "Recommended Weight (%)": "{:.1f}%"
                        }),
                        width="stretch",
                    )
                else:
                    st.error(
                        "Optimization failed. Please check your selected tickers or"
                        " network connection."
                    )
            else:
                st.warning(
                    "Select at least 2 different stocks in your portfolio to run"
                    " optimization."
                )

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("Your current portfolio is empty. Add shares above!")

elif menu_choice == "Database Commitment":
    st.markdown('<div class="fintech-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-title">💾 Save Asset to SQLite Database</div>',
        unsafe_allow_html=True,
    )

    col_add1, col_add2 = st.columns([2, 1])
    with col_add1:
        ticker_input = st.text_input("Add single ticker to database")
    with col_add2:
        st.write("")
        st.write("")
        save_button = st.button("Save single asset")

    if save_button:
        my_stock = Stock(ticker_input)
        price = my_stock.get_latest_price()
        if price is not None:
            my_portfolio.add_asset_price(my_stock, price)
            st.success(f"Stock saved {my_stock.ticker_symbol} : ${price}")
        else:
            st.error(f"Could not save {my_stock.ticker_symbol}")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="fintech-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-title">💼 Save Complete Portfolio Snapshot</div>',
        unsafe_allow_html=True,
    )

    # Invoerveld voor de portefeuillenaam
    portfolio_name_input = st.text_input("Name your portfolio snapshot", value="Mijn Hoofdportefeuille")

    if st.button("Save Entire Portfolio Snapshot"):
        if (
                "portfolio_holdings" in st.session_state
                and st.session_state.portfolio_holdings
        ):
            my_portfolio.save_portfolio_snapshot(
                st.session_state.portfolio_holdings,
                portfolio_name=portfolio_name_input
            )
            st.success(
                f"Portefeuille '{portfolio_name_input}' succesvol opgeslagen als snapshot!"
            )
        else:
            st.warning("No active portfolio found in session.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="fintech-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-title">🗄️ Database Overview & Local Chart</div>',
        unsafe_allow_html=True,
    )

    df = my_portfolio.get_history()

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"],format="mixed")

        # Bepaal automatisch of het om 'ticker' of 'asset' gaat
        col_name = "ticker" if "ticker" in df.columns else ("asset" if "asset" in df.columns else df.columns[1])

        # Bepaal automatisch welke prijkolom aanwezig is
        if "total_value" in df.columns:
            y_col = "total_value"
            label_y = "Total Value ($)"
        elif "unit_price" in df.columns:
            y_col = "unit_price"
            label_y = "Unit Price ($)"
        else:
            y_col = "price"
            label_y = "Price ($)"

        unique_assets = df[col_name].unique()
        selected_asset = st.selectbox(
            "Select a ticker from the database", unique_assets
        )

        df_filtered = df[df[col_name] == selected_asset].sort_values("timestamp")

        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor("#161b22")
        ax.set_facecolor("#161b22")

        ax.plot(
            df_filtered["timestamp"],
            df_filtered[y_col],
            marker="o",
            linestyle="-",
            color="#58a6ff",
            linewidth=2,
        )
        ax.set_title(
            f"Saved serie {selected_asset}", color="#e6edf3", fontweight="bold"
        )
        ax.set_xlabel("Time", color="#e6edf3")
        ax.set_ylabel(label_y, color="#e6edf3")
        ax.tick_params(colors="#e6edf3")
        ax.grid(True, linestyle="--", alpha=0.2)

        for spine in ax.spines.values():
            spine.set_color("#30363d")

        plt.xticks(rotation=45)
        fig.tight_layout()
        st.pyplot(fig)

        with st.expander("Show complete database table"):
            st.dataframe(df, width="stretch")
    else:
        st.info("No records in the database yet. Add your first share above!")

    st.markdown("</div>", unsafe_allow_html=True)

elif menu_choice == "AI Portfolio Analyst":
    st.subheader("🤖 AI Portfolio & Risk Analyst (Groq)")

    st.markdown('<div class="fintech-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-title">💬 Vraag het de AI Portefeuille Expert</div>',
        unsafe_allow_html=True,
    )
    st.write(
        "De AI analyseert direct jouw actuele portefeuille via de officiële"
        " Groq-client."
    )

    if "GROQ_API_KEY" in st.secrets:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])

            portfolio_context = (
                str(st.session_state.get("portfolio_holdings", {}))
                if "portfolio_holdings" in st.session_state
                else "Geen portefeuille geladen."
            )

            user_question = st.text_input(
                "Ask a question about your portfolio:",
                value=(
                    "Analyze my current portfolio holdings and give improvements"
                    " about risk diversion"
                ),
            )

            if st.button("Ask AI analyst"):
                with st.spinner("Analysing with Groq..."):
                    prompt = f"""
                    You are a professional quantitative portfolio manager and analyst. 
                    Give deep, sharp and fundamental improvements to the following portfolio and five ultimate stock/etf recommendations
                    of companies that have good solvency ratios, profit and sales growth, strong margins, postive free cash flow, 
                    strong product brand and market share or upcoming high potential:
                    {portfolio_context}
                    
                    User question: {user_question}
                    """

                    response = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                    )

                    ai_antwoord = response.choices[0].message.content

                    st.markdown("### 📊 AI Analysis & Advice:")
                    st.info(ai_antwoord)

        except Exception as e:
            st.error(f"Error starting Groq Client: {e}")
    else:
        st.warning("No `GROQ_API_KEY` found in Streamlit `secrets.toml`.")

    st.markdown("</div>", unsafe_allow_html=True)