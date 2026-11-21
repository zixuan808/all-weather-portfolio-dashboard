
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from datetime import date, timedelta
from html import escape


# ============================================================
# 1. SETTINGS
# ============================================================

st.set_page_config(
    page_title="All Weather Portfolio | Performance and Risk Analysis",
    layout="wide",
    initial_sidebar_state="collapsed"
)

INITIAL_INVESTMENT = 1_000_000
TRADING_DAYS = 252
CACHE_SECONDS = 900
FALLBACK_RF = 0.02

TODAY = date.today()
DOWNLOAD_END = (TODAY + timedelta(days=1)).isoformat()

PORTFOLIOS = [
    "All Weather",
    "S&P 500",
    "60/40 Portfolio"
]

COLORS = {
    "All Weather": "#245A81",
    "S&P 500": "#C17B38",
    "60/40 Portfolio": "#A0A8B0"
}

ASSETS = {
    "VTI": "US Equities",
    "TLT": "Long-Term US Treasuries",
    "IEF": "Intermediate-Term US Treasuries",
    "GLD": "Gold",
    "DBC": "Commodities"
}

ALL_WEATHER = {
    "VTI": 0.30,
    "TLT": 0.40,
    "IEF": 0.15,
    "GLD": 0.075,
    "DBC": 0.075
}

BALANCED = {
    "VTI": 0.60,
    "IEF": 0.40
}

TICKERS = list(ALL_WEATHER)
ALL_TICKERS = TICKERS + ["SPY"]


# ============================================================
# 2. DESIGN
# ============================================================

st.markdown("""
<style>
html, body, .stApp,
[data-testid="stAppViewContainer"] {
    background: #FFFFFF !important;
    color: #222831 !important;
    font-family: Arial, sans-serif !important;
}

.block-container {
    max-width: 1480px !important;
    padding: 30px 28px 25px !important;
    margin: auto !important;
}

h1 {
    font-size: 29px !important;
    font-weight: 700 !important;
    color: #1F2933 !important;
    line-height: 1.25 !important;
}

.report-subtitle {
    font-size: 15px;
    color: #637181;
    margin-bottom: 15px;
}

.metric-box {
    background: #F7F9FB;
    border: 1px solid #DFE5EB;
    border-radius: 6px;
    padding: 16px 18px;
    height: 115px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.metric-label {
    display: flex;
    align-items: center;
    gap: 7px;
    min-height: 38px;
    font-size: 14px;
    font-weight: 500;
    line-height: 1.3;
    color: #586674;
}

.metric-value {
    font-size: 25px;
    font-weight: 700;
    line-height: 1.2;
    color: #1F2933;
    white-space: nowrap;
}

.panel-heading {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 30px;
    margin-bottom: 4px;
}

.panel-title {
    font-size: 18px;
    font-weight: 600;
    color: #1F2933;
}

.chart-help {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border: 1px solid #A4B0BC;
    border-radius: 50%;
    color: #637181;
    background: white;
    font-size: 12px;
    font-weight: 700;
    cursor: help;
    flex-shrink: 0;
}

.chart-help .tooltip-text {
    visibility: hidden;
    opacity: 0;
    position: absolute;
    z-index: 9999;
    bottom: calc(100% + 9px);
    left: 50%;
    transform: translateX(-50%);
    width: 215px;
    max-width: 75vw;
    padding: 9px 11px;
    border-radius: 5px;
    background: #263746;
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 400;
    line-height: 1.4;
    text-align: left;
    white-space: normal;
    pointer-events: none;
    box-shadow: 0 3px 10px rgba(0,0,0,0.12);
}

.chart-help:hover .tooltip-text,
.chart-help:focus .tooltip-text {
    visibility: visible;
    opacity: 1;
}

[data-testid="stDownloadButton"] button {
    background: #FFFFFF !important;
    color: #245A81 !important;
    border: 1px solid #C8D4DE !important;
    border-radius: 5px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    width: 100%;
}

@media (max-width: 900px) {
    .block-container {
        padding: 20px 12px !important;
    }
    .metric-box {
        padding: 12px;
    }
    .metric-value {
        font-size: 20px;
    }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. TOOLTIP EXPLANATIONS
# ============================================================

EXPLANATIONS = {
    "Annualized Return":
        "Compounded average yearly return.",
    "Volatility":
        "Annualized standard deviation of returns.",
    "Sharpe Ratio":
        "Excess return per unit of total volatility.",
    "Maximum Drawdown":
        "Largest decline from a previous peak.",
    "Total Return":
        "Cumulative gain or loss over the period.",
    "60/40 Annualized Return":
        "Compounded yearly return of the 60/40 portfolio.",
    "Sortino Ratio":
        "Excess return per unit of downside risk.",
    "Daily VaR (95%)":
        "Daily loss threshold exceeded on 5% of historical days.",
    "Daily CVaR (95%)":
        "Average loss beyond the 95% VaR threshold.",
    "vs. S&P 500":
        "Annualized return difference in percentage points.",
    "vs. 60/40 Portfolio":
        "Annualized return difference in percentage points.",
    "Growth of a $1 Million Investment":
        "Hypothetical growth of an initial $1 million.",
    "Target Asset Allocation":
        "Target percentage invested in each asset class.",
    "Performance Comparison":
        "Compares portfolio returns and risk.",
    "Calendar-Year Returns":
        "Returns for each calendar year.",
    "Rolling 12-Month Returns":
        "Returns over the preceding 252 trading days.",
    "Monthly Returns (%)":
        "Monthly gains and losses of All Weather.",
    "Historical Drawdowns":
        "Declines from previous portfolio peaks.",
    "63-Day Rolling Volatility":
        "Annualized volatility over 63 trading days.",
    "252-Day Rolling Sharpe Ratio":
        "Risk-adjusted performance over 252 trading days.",
    "Daily Return Distribution":
        "Distribution of daily returns across all three portfolios.",
    "Asset Correlations":
        "How ETF returns move together, from -1 to +1.",
    "Risk Comparison":
        "Compares risk across the three portfolios."
}


# ============================================================
# 4. MARKET DATA
# ============================================================

@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def load_market_data(end_date):

    raw = yf.download(
        ALL_TICKERS,
        start="2006-01-01",
        end=end_date,
        auto_adjust=True,
        progress=False,
        threads=True
    )

    if raw.empty:
        raise ValueError("Yahoo Finance returned no data.")

    if not isinstance(raw.columns, pd.MultiIndex):
        raise ValueError("Unexpected Yahoo Finance format.")

    prices = raw["Close"]

    missing = [
        t for t in ALL_TICKERS
        if t not in prices.columns
    ]

    if missing:
        raise ValueError(
            "Missing market data: " + ", ".join(missing)
        )

    prices = (
        prices.reindex(columns=ALL_TICKERS)
        .sort_index()
        .dropna()
    )

    prices.index = pd.to_datetime(prices.index)

    if prices.index.tz is not None:
        prices.index = prices.index.tz_localize(None)

    prices = prices.loc[
        prices.index <= pd.Timestamp(date.today())
    ]

    if prices.empty:
        raise ValueError("No common trading dates.")

    return prices


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def load_risk_free(end_date):

    try:
        raw = yf.download(
            "^IRX",
            start="2006-01-01",
            end=end_date,
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if raw.empty:
            return pd.Series(dtype=float)

        if isinstance(raw.columns, pd.MultiIndex):
            rates = raw["Close"].iloc[:, 0]
        else:
            rates = raw["Close"]

        rates = pd.to_numeric(
            rates, errors="coerce"
        ).dropna()

        rates.index = pd.to_datetime(rates.index)

        if rates.index.tz is not None:
            rates.index = rates.index.tz_localize(None)

        return rates.sort_index()

    except Exception:
        return pd.Series(dtype=float)


with st.spinner("Loading historical market data..."):
    try:
        full_prices = load_market_data(DOWNLOAD_END)
        treasury_yield = load_risk_free(DOWNLOAD_END)
    except Exception as error:
        st.error(f"Market data error: {error}")
        st.stop()

if len(full_prices) < TRADING_DAYS:
    st.error("Insufficient historical data.")
    st.stop()

FIRST_DATE = full_prices.index[0]
LATEST_DATE = full_prices.index[-1]


# ============================================================
# 5. HEADER AND PERIOD
# ============================================================

title_col, download_col = st.columns([5, 1])

with title_col:
    st.title(
        "Ray Dalio's All Weather Portfolio: "
        "Performance and Risk Analysis"
    )

with download_col:
    st.write("")
    download_placeholder = st.empty()

st.markdown(
    '<div class="report-subtitle">'
    'Historical performance, diversification and downside risk'
    '</div>',
    unsafe_allow_html=True
)

period_col, _ = st.columns([1, 2])

with period_col:
    selected_period = st.selectbox(
        "Analysis period",
        [
            "1 year",
            "3 years",
            "5 years",
            "10 years",
            "Maximum available",
            "Custom range"
        ],
        index=4
    )

if selected_period == "Custom range":

    a, b = st.columns(2)

    with a:
        custom_start = st.date_input(
            "Start date",
            value=max(FIRST_DATE.date(), date(2015, 1, 1)),
            min_value=FIRST_DATE.date(),
            max_value=LATEST_DATE.date()
        )

    with b:
        custom_end = st.date_input(
            "End date",
            value=LATEST_DATE.date(),
            min_value=FIRST_DATE.date(),
            max_value=LATEST_DATE.date()
        )

    selected_start = pd.Timestamp(custom_start)
    selected_end = pd.Timestamp(custom_end)

elif selected_period == "Maximum available":

    selected_start = FIRST_DATE
    selected_end = LATEST_DATE

else:

    years = {
        "1 year": 1,
        "3 years": 3,
        "5 years": 5,
        "10 years": 10
    }[selected_period]

    selected_end = LATEST_DATE
    selected_start = (
        selected_end - pd.DateOffset(years=years)
    )

if selected_start >= selected_end:
    st.error("Start date must be before end date.")
    st.stop()

selected_prices = full_prices.loc[
    (full_prices.index >= selected_start) &
    (full_prices.index <= selected_end)
].copy()

if len(selected_prices) < 20:
    st.error("Select a longer analysis period.")
    st.stop()

daily_returns = selected_prices.pct_change(
    fill_method=None
).dropna()

analysis_start = selected_prices.index[0]
analysis_end = selected_prices.index[-1]

st.caption(
    f"Analysis period: {analysis_start:%d %b %Y} "
    f"to {analysis_end:%d %b %Y} | "
    f"Latest market data: {LATEST_DATE:%d %b %Y}"
)


# ============================================================
# 6. RISK-FREE RATE
# ============================================================

if treasury_yield.empty:

    rf_series = pd.Series(
        np.nan,
        index=daily_returns.index
    )

else:

    rf_series = treasury_yield.reindex(
        daily_returns.index,
        method="ffill"
    )

if rf_series.notna().all():

    daily_rf = (
        (1 + rf_series / 100)
        ** (1 / TRADING_DAYS) - 1
    )

    rf_source = "Historical 13-week Treasury bill yield proxy"

else:

    daily_rf = pd.Series(
        (1 + FALLBACK_RF) ** (1 / TRADING_DAYS) - 1,
        index=daily_returns.index
    )

    rf_source = "Assumed 2% annual risk-free rate"


# ============================================================
# 7. PORTFOLIO SIMULATION
# ============================================================

@st.cache_data(show_spinner=False)
def simulate_portfolio(returns, weights):

    target = pd.Series(weights, dtype=float)
    current = target.copy()

    previous_year = None
    values = []

    for dt, row in returns.iterrows():

        if dt.year != previous_year:
            current = target.copy()
            previous_year = dt.year

        portfolio_return = (
            row[target.index] * current
        ).sum()

        values.append(portfolio_return)

        current = (
            current * (1 + row[target.index])
        ) / (1 + portfolio_return)

    return pd.Series(values, index=returns.index)


all_weather_returns = simulate_portfolio(
    daily_returns,
    ALL_WEATHER
)

balanced_returns = simulate_portfolio(
    daily_returns,
    BALANCED
)

return_data = pd.DataFrame({
    "All Weather": all_weather_returns,
    "S&P 500": daily_returns["SPY"],
    "60/40 Portfolio": balanced_returns
}).dropna()

daily_rf = daily_rf.reindex(
    return_data.index
).ffill()


# ============================================================
# 8. FINANCIAL METRICS
# ============================================================

def calculate_metrics(r):

    wealth = (1 + r).cumprod()

    years = max(
        (r.index[-1] - analysis_start).days / 365.25,
        1 / 365.25
    )

    total_return = wealth.iloc[-1] - 1
    cagr = wealth.iloc[-1] ** (1 / years) - 1
    volatility = r.std() * np.sqrt(TRADING_DAYS)

    excess = r - daily_rf

    sharpe = (
        excess.mean() * TRADING_DAYS / volatility
        if volatility > 0 else np.nan
    )

    downside = np.minimum(excess, 0)

    downside_deviation = (
        np.sqrt(np.mean(downside ** 2))
        * np.sqrt(TRADING_DAYS)
    )

    sortino = (
        excess.mean() * TRADING_DAYS / downside_deviation
        if downside_deviation > 0 else np.nan
    )

    wealth_with_start = pd.concat([
        pd.Series([1.0], index=[analysis_start]),
        wealth
    ])

    drawdown = (
        wealth_with_start /
        wealth_with_start.cummax() - 1
    )

    var_95 = r.quantile(0.05)
    cvar_95 = r[r <= var_95].mean()

    return {
        "Total Return": total_return,
        "Annualized Return": cagr,
        "Volatility": volatility,
        "Sharpe Ratio": sharpe,
        "Sortino Ratio": sortino,
        "Maximum Drawdown": drawdown.min(),
        "Daily VaR (95%)": -var_95,
        "Daily CVaR (95%)": -cvar_95
    }


results = pd.DataFrame({
    name: calculate_metrics(return_data[name])
    for name in PORTFOLIOS
})

metrics = results["All Weather"]

excess_vs_sp500 = (
    results.loc["Annualized Return", "All Weather"]
    - results.loc["Annualized Return", "S&P 500"]
) * 100

excess_vs_balanced = (
    results.loc["Annualized Return", "All Weather"]
    - results.loc["Annualized Return", "60/40 Portfolio"]
) * 100


# ============================================================
# 9. CHART DATA
# ============================================================

growth = (
    (1 + return_data).cumprod()
    * INITIAL_INVESTMENT
)

initial_row = pd.DataFrame(
    [{name: INITIAL_INVESTMENT for name in PORTFOLIOS}],
    index=[analysis_start]
)

growth = pd.concat([initial_row, growth])

drawdowns = (
    growth.div(growth.cummax()).sub(1) * 100
)

rolling_volatility = (
    return_data.rolling(63).std()
    * np.sqrt(TRADING_DAYS) * 100
)

rolling_returns = (
    (1 + return_data)
    .rolling(252)
    .apply(np.prod, raw=True) - 1
) * 100

rolling_excess = return_data.sub(
    daily_rf,
    axis=0
)

rolling_sharpe = (
    rolling_excess.rolling(252).mean()
    * TRADING_DAYS
) / (
    return_data.rolling(252).std()
    * np.sqrt(TRADING_DAYS)
).replace(0, np.nan)

annual_returns = (
    (1 + return_data)
    .resample("YE")
    .prod() - 1
) * 100

annual_labels = []

for year in annual_returns.index.year:

    label = str(year)

    year_prices = full_prices.loc[
        full_prices.index.year == year
    ]

    if not year_prices.empty:

        if (
            year == analysis_start.year
            and analysis_start > year_prices.index[0]
        ):
            label += " (partial)"

        if (
            year == analysis_end.year
            and analysis_end < year_prices.index[-1]
        ):
            if "partial" not in label:
                label += " (partial)"

        elif (
            year == analysis_end.year
            and analysis_end.month != 12
        ):
            if "partial" not in label:
                label += " (YTD)"

    annual_labels.append(label)

annual_returns.index = annual_labels

monthly_returns = (
    (1 + return_data)
    .resample("ME")
    .prod() - 1
) * 100

monthly_table = pd.DataFrame({
    "Year": monthly_returns.index.year,
    "Month": monthly_returns.index.month,
    "Return": monthly_returns["All Weather"].values
}).pivot(
    index="Year",
    columns="Month",
    values="Return"
).reindex(columns=range(1, 13))

monthly_table.columns = [
    "Jan", "Feb", "Mar", "Apr",
    "May", "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov", "Dec"
]

allocation = pd.DataFrame({
    "ETF": TICKERS,
    "Asset Class": [ASSETS[t] for t in TICKERS],
    "Weight": [ALL_WEATHER[t] for t in TICKERS]
})

monthly_growth = pd.concat([
    growth.iloc[[0]],
    growth.resample("ME").last()
]).sort_index()

monthly_growth = monthly_growth[
    ~monthly_growth.index.duplicated(keep="first")
]

monthly_volatility = (
    rolling_volatility.resample("ME").mean()
)

monthly_sharpe = (
    rolling_sharpe.resample("ME").mean()
)

monthly_rolling_returns = (
    rolling_returns.resample("ME").last()
)

correlations = daily_returns[TICKERS].corr()


# ============================================================
# 10. DISPLAY HELPERS
# ============================================================

def help_icon(explanation):

    safe = escape(explanation, quote=True)

    return (
        '<span class="chart-help" tabindex="0" '
        f'aria-label="{safe}">'
        '?'
        f'<span class="tooltip-text">{safe}</span>'
        '</span>'
    )


def chart_heading(title):

    explanation = EXPLANATIONS.get(title, "")

    st.markdown(
        '<div class="panel-heading">'
        f'<span class="panel-title">{escape(title)}</span>'
        f'{help_icon(explanation)}'
        '</div>',
        unsafe_allow_html=True
    )


def metric_card(column, label, value):

    explanation = EXPLANATIONS.get(label, "")

    column.markdown(
        '<div class="metric-box">'
        '<div class="metric-label">'
        f'<span>{escape(label)}</span>'
        f'{help_icon(explanation)}'
        '</div>'
        '<div class="metric-value">'
        f'{escape(str(value))}'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


def style_chart(fig, height=330):

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(
            family="Arial",
            size=13,
            color="#39434D"
        ),
        margin=dict(l=35, r=20, t=20, b=55),
        height=height,
        legend=dict(
            orientation="h",
            y=-0.30,
            x=0.5,
            xanchor="center"
        )
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#D7DEE5"
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#EFF2F5"
    )

    return fig


def make_line_chart(data, y_label):

    fig = go.Figure()

    for name in PORTFOLIOS:

        if name not in data.columns:
            continue

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data[name],
                mode="lines",
                name=name,
                line=dict(
                    color=COLORS[name],
                    width=3 if name == "All Weather" else 2,
                    dash=(
                        "dash"
                        if name == "60/40 Portfolio"
                        else "solid"
                    )
                ),
                connectgaps=False
            )
        )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=y_label,
        hovermode="x unified"
    )

    return style_chart(fig)


def chart_panel(title, fig):

    with st.container(border=True):

        chart_heading(title)

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False}
        )


# ============================================================
# 11. CHARTS
# ============================================================

comparison_chart = make_line_chart(
    monthly_growth,
    "Investment value (USD)"
)

comparison_chart.update_yaxes(
    tickprefix="$",
    tickformat=",.0f"
)

drawdown_chart = make_line_chart(
    drawdowns,
    "Drawdown (%)"
)

volatility_chart = make_line_chart(
    monthly_volatility,
    "Annualized volatility (%)"
)

sharpe_chart = make_line_chart(
    monthly_sharpe,
    "Rolling Sharpe ratio"
)

rolling_chart = make_line_chart(
    monthly_rolling_returns,
    "Rolling return (%)"
)

pie_chart = go.Figure(
    go.Pie(
        labels=allocation["Asset Class"],
        values=allocation["Weight"],
        hole=0.48,
        sort=False,
        textinfo="percent",
        textposition="outside",
        marker=dict(
            colors=[
                "#6073E8",
                "#E65A45",
                "#16B894",
                "#A65BE3",
                "#F59B56"
            ]
        )
    )
)

style_chart(pie_chart)

annual_chart = go.Figure()

for name in PORTFOLIOS:

    annual_chart.add_trace(
        go.Bar(
            x=annual_returns.index,
            y=annual_returns[name],
            name=name,
            marker_color=COLORS[name]
        )
    )

annual_chart.update_layout(
    barmode="group",
    xaxis_title="Year",
    yaxis_title="Return (%)"
)

style_chart(annual_chart)

heatmap_chart = go.Figure(
    go.Heatmap(
        z=monthly_table.values,
        x=monthly_table.columns,
        y=monthly_table.index,
        colorscale="RdYlGn",
        zmid=0,
        colorbar=dict(title="%"),
        hovertemplate=(
            "Year %{y}<br>%{x}: "
            "%{z:.2f}%<extra></extra>"
        )
    )
)

style_chart(heatmap_chart, 340)

correlation_chart = go.Figure(
    go.Heatmap(
        z=correlations.values,
        x=correlations.columns,
        y=correlations.index,
        zmin=-1,
        zmax=1,
        colorscale="RdBu",
        reversescale=True,
        colorbar=dict(
            thickness=13,
            len=0.85
        )
    )
)

for i, ticker_y in enumerate(TICKERS):
    for j, ticker_x in enumerate(TICKERS):

        value = correlations.iloc[i, j]

        correlation_chart.add_annotation(
            x=ticker_x,
            y=ticker_y,
            text=f"{value:.2f}",
            showarrow=False,
            font=dict(
                size=12,
                color=(
                    "white"
                    if abs(value) > 0.65
                    else "#25313D"
                )
            )
        )

style_chart(correlation_chart)

correlation_chart.update_layout(
    margin=dict(l=45, r=20, t=20, b=55)
)

distribution_chart = go.Figure()

for name in PORTFOLIOS:

    distribution_chart.add_trace(
        go.Histogram(
            x=return_data[name] * 100,
            name=name,
            marker_color=COLORS[name],
            opacity=0.55,
            nbinsx=60,
            histnorm="probability density"
        )
    )

distribution_chart.add_vline(
    x=-metrics["Daily VaR (95%)"] * 100,
    line_dash="dash",
    line_color="#B64A4A"
)

distribution_chart.update_layout(
    barmode="overlay",
    xaxis_title="Daily return (%)",
    yaxis_title="Probability density"
)

style_chart(distribution_chart)


# ============================================================
# 12. COMPARISON TABLES
# ============================================================

PERCENTAGE_METRICS = [
    "Total Return",
    "Annualized Return",
    "Volatility",
    "Maximum Drawdown",
    "Daily VaR (95%)",
    "Daily CVaR (95%)"
]


def make_comparison_table(metric_list):

    labels = []
    values = {name: [] for name in PORTFOLIOS}

    for metric in metric_list:

        label = (
            metric + " (%)"
            if metric in PERCENTAGE_METRICS
            else metric
        )

        labels.append(label)

        for portfolio in PORTFOLIOS:

            value = results.loc[metric, portfolio]

            if metric in PERCENTAGE_METRICS:
                formatted = f"{value:.2%}"
            else:
                formatted = f"{value:.2f}"

            values[portfolio].append(formatted)

    header_height = 52
    row_height = 55

    table_height = (
        header_height +
        len(metric_list) * row_height +
        12
    )

    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[39, 21, 19, 21],
                header=dict(
                    values=[
                        "<b>Metric</b>",
                        "<b>All Weather</b>",
                        "<b>S&P 500</b>",
                        "<b>60/40 Portfolio</b>"
                    ],
                    align=[
                        "left", "right", "right", "right"
                    ],
                    fill_color="#F7F9FB",
                    line_color="#D9E0E7",
                    font=dict(
                        family="Arial",
                        size=14,
                        color="#526171"
                    ),
                    height=header_height
                ),
                cells=dict(
                    values=[
                        labels,
                        values["All Weather"],
                        values["S&P 500"],
                        values["60/40 Portfolio"]
                    ],
                    align=[
                        "left", "right", "right", "right"
                    ],
                    fill_color="#FFFFFF",
                    line_color="#E9EDF1",
                    font=dict(
                        family="Arial",
                        size=14,
                        color="#25313D"
                    ),
                    height=row_height
                )
            )
        ]
    )

    fig.update_layout(
        height=table_height,
        margin=dict(l=0, r=0, t=5, b=5),
        paper_bgcolor="#FFFFFF"
    )

    return fig


overview_table = make_comparison_table([
    "Total Return",
    "Annualized Return",
    "Volatility",
    "Sharpe Ratio",
    "Maximum Drawdown"
])

risk_table = make_comparison_table([
    "Volatility",
    "Sharpe Ratio",
    "Sortino Ratio",
    "Maximum Drawdown",
    "Daily VaR (95%)",
    "Daily CVaR (95%)"
])

pie_chart.update_layout(
    height=overview_table.layout.height
)

correlation_chart.update_layout(
    height=risk_table.layout.height
)


# ============================================================
# 13. CSV DOWNLOAD
# ============================================================

def prepare_export():

    export = selected_prices.add_prefix(
        "Adjusted_Price_"
    ).copy()

    export = export.join(
        (daily_returns * 100).add_prefix(
            "ETF_Return_pct_"
        )
    )

    export = export.join(
        (return_data * 100).add_prefix(
            "Portfolio_Return_pct_"
        )
    )

    export = export.join(
        growth.add_prefix(
            "Investment_Value_USD_"
        )
    )

    export = export.join(
        drawdowns.add_prefix(
            "Drawdown_pct_"
        )
    )

    export = export.join(
        rolling_volatility.add_prefix(
            "Rolling_Volatility_pct_"
        )
    )

    export = export.join(
        rolling_sharpe.add_prefix(
            "Rolling_Sharpe_"
        )
    )

    export = export.join(
        rolling_returns.add_prefix(
            "Rolling_12M_Return_pct_"
        )
    )

    export["Risk_Free_Daily_pct"] = daily_rf * 100

    # Store period-wide metrics once, in the first row.
    for portfolio in PORTFOLIOS:

        prefix = (
            portfolio.replace(" ", "_")
            .replace("/", "_")
        )

        for metric in results.index:

            value = results.loc[metric, portfolio]

            if metric in PERCENTAGE_METRICS:
                value *= 100

            metric_name = (
                metric.replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
                .replace("%", "pct")
            )

            column = f"Summary_{prefix}_{metric_name}"

            export[column] = np.nan
            export.loc[export.index[0], column] = value

    for ticker, weight in ALL_WEATHER.items():

        column = f"Target_Weight_pct_{ticker}"

        export[column] = np.nan
        export.loc[export.index[0], column] = weight * 100

    for ticker_y in TICKERS:
        for ticker_x in TICKERS:

            column = f"Correlation_{ticker_y}_{ticker_x}"

            export[column] = np.nan
            export.loc[
                export.index[0], column
            ] = correlations.loc[ticker_y, ticker_x]

    export.index.name = "Date"

    return export.to_csv(
        na_rep="",
        float_format="%.8f"
    ).encode("utf-8-sig")


download_placeholder.download_button(
    label="Download CSV",
    data=prepare_export(),
    file_name=(
        f"all_weather_dashboard_"
        f"{analysis_start:%Y%m%d}_"
        f"{analysis_end:%Y%m%d}.csv"
    ),
    mime="text/csv"
)


# ============================================================
# 14. DASHBOARD TABS
# ============================================================

st.divider()

tab1, tab2, tab3 = st.tabs([
    "Overview",
    "Performance",
    "Risk Analysis"
])


# ============================================================
# 15. OVERVIEW
# ============================================================

with tab1:

    c1, c2, c3, c4 = st.columns(4)

    metric_card(
        c1,
        "Annualized Return",
        f"{metrics['Annualized Return']:.2%}"
    )

    metric_card(
        c2,
        "Volatility",
        f"{metrics['Volatility']:.2%}"
    )

    metric_card(
        c3,
        "Sharpe Ratio",
        f"{metrics['Sharpe Ratio']:.2f}"
    )

    metric_card(
        c4,
        "Maximum Drawdown",
        f"{metrics['Maximum Drawdown']:.2%}"
    )

    st.write("")

    chart_panel(
        "Growth of a $1 Million Investment",
        comparison_chart
    )

    left, right = st.columns(2, gap="small")

    with left:
        chart_panel(
            "Target Asset Allocation",
            pie_chart
        )

    with right:
        chart_panel(
            "Performance Comparison",
            overview_table
        )


# ============================================================
# 16. PERFORMANCE
# ============================================================

with tab2:

    c1, c2, c3 = st.columns(3)

    metric_card(
        c1,
        "Total Return",
        f"{metrics['Total Return']:.2%}"
    )

    metric_card(
        c2,
        "Annualized Return",
        f"{metrics['Annualized Return']:.2%}"
    )

    metric_card(
        c3,
        "60/40 Annualized Return",
        f"{results.loc['Annualized Return', '60/40 Portfolio']:.2%}"
    )

    st.write("")

    st.markdown("#### Benchmark Outperformance")

    b1, b2 = st.columns(2)

    metric_card(
        b1,
        "vs. S&P 500",
        f"{excess_vs_sp500:+.2f} pp"
    )

    metric_card(
        b2,
        "vs. 60/40 Portfolio",
        f"{excess_vs_balanced:+.2f} pp"
    )

    st.write("")

    left, right = st.columns(2, gap="small")

    with left:
        chart_panel(
            "Calendar-Year Returns",
            annual_chart
        )

    with right:
        chart_panel(
            "Rolling 12-Month Returns",
            rolling_chart
        )

    chart_panel(
        "Monthly Returns (%)",
        heatmap_chart
    )


# ============================================================
# 17. RISK ANALYSIS
# ============================================================

with tab3:

    c1, c2, c3, c4 = st.columns(4)

    metric_card(
        c1,
        "Sortino Ratio",
        f"{metrics['Sortino Ratio']:.2f}"
    )

    metric_card(
        c2,
        "Daily VaR (95%)",
        f"{metrics['Daily VaR (95%)']:.2%}"
    )

    metric_card(
        c3,
        "Daily CVaR (95%)",
        f"{metrics['Daily CVaR (95%)']:.2%}"
    )

    metric_card(
        c4,
        "Maximum Drawdown",
        f"{metrics['Maximum Drawdown']:.2%}"
    )

    st.write("")

    left, right = st.columns(2, gap="small")

    with left:
        chart_panel(
            "Historical Drawdowns",
            drawdown_chart
        )

    with right:
        chart_panel(
            "63-Day Rolling Volatility",
            volatility_chart
        )

    left, right = st.columns(2, gap="small")

    with left:
        chart_panel(
            "252-Day Rolling Sharpe Ratio",
            sharpe_chart
        )

    with right:
        chart_panel(
            "Daily Return Distribution",
            distribution_chart
        )

    left, right = st.columns(2, gap="small")

    with left:
        chart_panel(
            "Asset Correlations",
            correlation_chart
        )

    with right:
        chart_panel(
            "Risk Comparison",
            risk_table
        )


# ============================================================
# 18. METHODOLOGY AND ASSUMPTIONS
# ============================================================

st.divider()

with st.expander("Methodology and Assumptions"):

    st.markdown(f"""
### Portfolio Construction

The All Weather portfolio is approximated using five ETFs:

| Asset | ETF | Weight |
|---|---|---:|
| US Equities | VTI | 30% |
| Long-Term US Treasuries | TLT | 40% |
| Intermediate-Term US Treasuries | IEF | 15% |
| Gold | GLD | 7.5% |
| Commodities | DBC | 7.5% |

Performance is compared against two benchmarks:
the **S&P 500**, represented by the SPY ETF,
and a **60/40 Portfolio** comprising 60% VTI
and 40% IEF.

### Data and Backtesting

Historical adjusted closing prices are sourced
from Yahoo Finance through yfinance.

Each strategy starts with a hypothetical
**$1 million investment** at the first available
closing price in the selected period.

Daily returns are compounded, with portfolio
weights reset to their targets at the beginning
of the analysis and on the first return observation
of each subsequent calendar year.

### Performance and Risk Measurement

Annualized volatility, Sharpe and Sortino ratios
use 252 trading days per year.

Historical one-day Value at Risk (VaR) and
Conditional Value at Risk (CVaR) are estimated
at the 95% confidence level.

The risk-free rate uses the 13-week US Treasury
bill yield proxy where available; otherwise,
a 2% annual rate is assumed.

**Risk-free rate source:** {rf_source}.

### Assumptions and Limitations

The backtest assumes dividend-adjusted ETF prices,
fractional holdings and cost-free rebalancing.

It excludes transaction costs, taxes, inflation,
market impact and other implementation frictions.

SPY approximates the S&P 500 total return but may
differ from the official index because of fees
and tracking differences.

The All Weather allocation is a simplified
ETF representation, not Bridgewater's proprietary
institutional strategy.

**Past performance does not guarantee future results.**
""")


# ============================================================
# 19. FOOTER
# ============================================================

st.markdown(
    '<div style="font-size:13px;color:#637181;">'
    'Historical ETF portfolio backtest using Yahoo Finance data. '
    'The S&P 500 benchmark uses SPY as its total-return proxy. '
    'Performance is hypothetical and excludes trading costs.'
    '</div>',
    unsafe_allow_html=True
)
