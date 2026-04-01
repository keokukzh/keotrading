"""
KEOTrading Dashboard - Backtest Page
Strategy backtesting and performance comparison.
"""

from __future__ import annotations

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# Mock backtest results
MOCK_BACKTEST_RESULTS = {
    "BTC/USDT": {
        "mean_reversion": {
            "total_return": 4521.30,
            "return_pct": 45.21,
            "sharpe_ratio": 1.84,
            "max_drawdown": -8.5,
            "win_rate": 62.3,
            "profit_factor": 2.1,
            "total_trades": 156,
            "avg_trade": 29.00,
        },
        "momentum": {
            "total_return": 8234.50,
            "return_pct": 82.35,
            "sharpe_ratio": 2.41,
            "max_drawdown": -12.3,
            "win_rate": 48.2,
            "profit_factor": 2.8,
            "total_trades": 89,
            "avg_trade": 92.50,
        },
        "grid": {
            "total_return": 2341.20,
            "return_pct": 23.41,
            "sharpe_ratio": 1.52,
            "max_drawdown": -5.2,
            "win_rate": 71.5,
            "profit_factor": 1.9,
            "total_trades": 312,
            "avg_trade": 7.50,
        },
        "llm_enhanced": {
            "total_return": 6156.80,
            "return_pct": 61.57,
            "sharpe_ratio": 2.12,
            "max_drawdown": -9.8,
            "win_rate": 58.4,
            "profit_factor": 2.4,
            "total_trades": 124,
            "avg_trade": 49.65,
        },
    },
    "ETH/USDT": {
        "mean_reversion": {
            "total_return": 3892.10,
            "return_pct": 38.92,
            "sharpe_ratio": 1.65,
            "max_drawdown": -7.8,
            "win_rate": 59.1,
            "profit_factor": 1.95,
            "total_trades": 203,
            "avg_trade": 19.17,
        },
        "momentum": {
            "total_return": 5678.90,
            "return_pct": 56.79,
            "sharpe_ratio": 1.98,
            "max_drawdown": -11.2,
            "win_rate": 51.3,
            "profit_factor": 2.2,
            "total_trades": 67,
            "avg_trade": 84.76,
        },
    }
}


def generate_mock_equity_curve(strategy: str, pair: str) -> pd.DataFrame:
    """Generate mock equity curve data."""
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(90, -1, -1)]
    
    if strategy == "mean_reversion":
        base = 10000
        volatility = 0.015
    elif strategy == "momentum":
        base = 10000
        volatility = 0.025
    elif strategy == "grid":
        base = 10000
        volatility = 0.008
    else:
        base = 10000
        volatility = 0.018
    
    values = []
    current = base
    import random
    for i in range(91):
        daily_return = random.uniform(-volatility, volatility * 1.5)
        if strategy == "momentum" and i > 45:
            daily_return += 0.01  # Trending up
        elif strategy == "mean_reversion" and abs(current - base) > base * 0.05:
            daily_return -= 0.005  # Reversion
        current *= (1 + daily_return)
        values.append(current)
    
    return pd.DataFrame({"date": dates, "equity": values})


def render_backtest_page():
    """Render the Backtest page."""
    st.title("📈 Backtesting")
    st.markdown("Test and validate trading strategies on historical data.")
    st.markdown("---")
    
    # Configuration
    config_col1, config_col2, config_col3 = st.columns([1, 1, 1])
    
    with config_col1:
        selected_pair = st.selectbox(
            "Trading Pair",
            ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "LINK/USDT"]
        )
    
    with config_col2:
        selected_strategy = st.selectbox(
            "Strategy",
            ["All", "Mean Reversion", "Momentum", "Grid", "LLM Enhanced", "Custom"]
        )
    
    with config_col3:
        timeframe = st.selectbox(
            "Timeframe",
            ["1H", "4H", "1D"]
        )
    
    # Date range
    date_col1, date_col2 = st.columns([1, 1])
    
    with date_col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().date() - timedelta(days=90)
        )
    
    with date_col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now().date()
        )
    
    # Parameters
    param_col1, param_col2, param_col3 = st.columns([1, 1, 1])
    
    with param_col1:
        initial_capital = st.number_input(
            "Initial Capital ($)",
            value=10000,
            min_value=1000,
            step=1000
        )
    
    with param_col2:
        fee_rate = st.number_input(
            "Fee Rate (%)",
            value=0.1,
            min_value=0.0,
            max_value=1.0,
            step=0.01
        ) / 100
    
    with param_col3:
        slippage = st.number_input(
            "Slippage (%)",
            value=0.05,
            min_value=0.0,
            max_value=1.0,
            step=0.01
        ) / 100
    
    # Run backtest button
    if st.button("🚀 Run Backtest", type="primary", use_container_width=True):
        with st.spinner("Running backtest..."):
            import time
            time.sleep(2)  # Simulate computation
            st.success("✅ Backtest completed!")
    
    st.markdown("---")
    
    # Results section
    if selected_strategy != "All":
        # Single strategy view
        strategy_key = selected_strategy.lower().replace(" ", "_")
        
        if selected_pair in MOCK_BACKTEST_RESULTS and strategy_key in MOCK_BACKTEST_RESULTS[selected_pair]:
            results = MOCK_BACKTEST_RESULTS[selected_pair][strategy_key]
            
            # Metrics
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric(
                    "Total Return",
                    f"${results['total_return']:,.2f}",
                    delta=f"{results['return_pct']:.2f}%"
                )
            
            with metric_col2:
                st.metric(
                    "Sharpe Ratio",
                    f"{results['sharpe_ratio']:.2f}"
                )
            
            with metric_col3:
                st.metric(
                    "Max Drawdown",
                    f"{results['max_drawdown']:.1f}%"
                )
            
            with metric_col4:
                st.metric(
                    "Win Rate",
                    f"{results['win_rate']:.1f}%"
                )
            
            st.markdown("---")
            
            # Charts
            chart_col1, chart_col2 = st.columns([2, 1])
            
            with chart_col1:
                st.subheader("Equity Curve")
                
                equity_df = generate_mock_equity_curve(strategy_key, selected_pair)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=equity_df["date"],
                    y=equity_df["equity"],
                    mode="lines",
                    fill="tozeroy",
                    line=dict(color="#00D4AA", width=2),
                    fillcolor="rgba(0, 212, 170, 0.1)",
                    name="Equity"
                ))
                
                # Add initial capital line
                fig.add_hline(
                    y=initial_capital,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text="Initial"
                )
                
                fig.update_layout(
                    height=350,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="$"),
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with chart_col2:
                st.subheader("Trade Statistics")
                
                stats_data = {
                    "Metric": ["Total Trades", "Winning", "Losing", "Avg Trade", "Profit Factor"],
                    "Value": [
                        results['total_trades'],
                        f"{int(results['total_trades'] * results['win_rate'] / 100)}",
                        f"{int(results['total_trades'] * (100 - results['win_rate']) / 100)}",
                        f"${results['avg_trade']:.2f}",
                        f"{results['profit_factor']:.2f}"
                    ]
                }
                
                st.dataframe(stats_data, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Monthly returns
            st.subheader("Monthly Returns")
            
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
            returns = [3.2, -1.5, 4.8, 2.1, -0.8, 3.5]
            colors = ["green" if r >= 0 else "red" for r in returns]
            
            monthly_df = pd.DataFrame({
                "Month": months,
                "Return": returns
            })
            
            fig = px.bar(
                monthly_df,
                x="Month",
                y="Return",
                color="Return",
                color_continuous_scale=["red", "green"],
                range_color=[-5, 5]
            )
            
            fig.update_layout(
                height=250,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info(f"No backtest results for {selected_strategy} on {selected_pair}")
    
    else:
        # Compare all strategies
        st.subheader("Strategy Comparison")
        
        strategies = ["Mean Reversion", "Momentum", "Grid", "LLM Enhanced"]
        
        comparison_data = []
        for strategy in strategies:
            strategy_key = strategy.lower().replace(" ", "_")
            
            if selected_pair in MOCK_BACKTEST_RESULTS and strategy_key in MOCK_BACKTEST_RESULTS[selected_pair]:
                results = MOCK_BACKTEST_RESULTS[selected_pair][strategy_key]
                
                comparison_data.append({
                    "Strategy": strategy,
                    "Return %": results['return_pct'],
                    "Sharpe": results['sharpe_ratio'],
                    "Max DD %": results['max_drawdown'],
                    "Win Rate %": results['win_rate'],
                    "Trades": results['total_trades'],
                    "Avg Trade $": results['avg_trade']
                })
        
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            
            # Sort by return
            comparison_df = comparison_df.sort_values("Return %", ascending=False)
            
            # Color code returns
            def color_returns(val):
                if val > 50:
                    return "background-color: rgba(0, 212, 170, 0.3)"
                elif val > 20:
                    return "background-color: rgba(0, 212, 170, 0.1)"
                elif val > 0:
                    return ""
                else:
                    return "background-color: rgba(255, 107, 107, 0.3)"
            
            st.dataframe(
                comparison_df.style.applymap(color_returns, subset=["Return %"]),
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            
            # Comparison chart
            chart_col1, chart_col2 = st.columns([1, 1])
            
            with chart_col1:
                st.subheader("Return Comparison")
                
                fig = px.bar(
                    comparison_df,
                    x="Strategy",
                    y="Return %",
                    color="Return %",
                    color_continuous_scale=["red", "yellow", "green"]
                )
                
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with chart_col2:
                st.subheader("Risk-Return Profile")
                
                fig = px.scatter(
                    comparison_df,
                    x="Max DD %",
                    y="Return %",
                    size="Trades",
                    color="Sharpe",
                    hover_name="Strategy",
                    color_continuous_scale=["red", "yellow", "green"]
                )
                
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Export options
    export_col1, export_col2, export_col3 = st.columns([1, 1, 2])
    
    with export_col1:
        if st.button("📥 Export Results", use_container_width=True):
            st.info("Export feature coming soon")
    
    with export_col2:
        if st.button("📊 Export Trades", use_container_width=True):
            st.info("Export feature coming soon")
    
    with export_col3:
        st.write()


if __name__ == "__main__":
    render_backtest_page()
