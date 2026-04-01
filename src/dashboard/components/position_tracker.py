"""
Position Tracker Component
Real-time position monitoring and management.
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.exchange.execution import Position, OrderExecutor, Trade


def render_position_card(position: Position) -> None:
    """Render a single position card."""
    pnl_color = "green" if position.pnl >= 0 else "red"
    pnl_pct_color = "green" if position.pnl_pct >= 0 else "red"
    
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.markdown(f"**{position.symbol}**")
            st.caption(f"{position.exchange_id.upper()} • {position.strategy}")
        
        with col2:
            st.metric(
                "Amount",
                f"{position.amount:.4f}",
                delta=f"Entry: ${position.entry_price:,.2f}"
            )
        
        with col3:
            st.metric(
                "Current",
                f"${position.current_price:,.2f}",
                delta=f"{position.pnl_pct:+.2f}%" if position.pnl_pct else None
            )
        
        with col4:
            st.metric(
                "P&L",
                f"${position.pnl + position.unrealized_pnl:,.2f}",
                delta=f"{position.pnl_pct:+.2f}%",
                delta_color="normal" if position.pnl_pct >= 0 else "inverse"
            )


def render_positions_list(positions: List[Position]) -> None:
    """Render list of positions."""
    if not positions:
        st.info("📭 No open positions")
        return
    
    # Summary
    total_value = sum(p.amount * p.current_price for p in positions)
    total_pnl = sum(p.pnl + p.unrealized_pnl for p in positions)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Open Positions", len(positions))
    with col2:
        st.metric("Total Value", f"${total_value:,.2f}")
    with col3:
        st.metric(
            "Total P&L",
            f"${total_pnl:,.2f}",
            delta_color="normal" if total_pnl >= 0 else "inverse"
        )
    
    st.markdown("---")
    
    # Position cards
    for pos in positions:
        render_position_card(pos)
        st.markdown("---")


def render_position_chart(positions: List[Position]) -> None:
    """Render position distribution chart."""
    if not positions:
        st.info("No positions to chart")
        return
    
    # Prepare data
    labels = [f"{p.symbol}" for p in positions]
    values = [p.amount * p.current_price for p in positions]
    colors = ["#00D4AA" if p.pnl_pct >= 0 else "#FF6B6B" for p in positions]
    
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "bar"}]],
        subplot_titles=["Allocation", "P&L by Position"]
    )
    
    # Pie chart
    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.5,
            marker_colors=colors
        ),
        row=1, col=1
    )
    
    # Bar chart
    pnl_values = [p.pnl + p.unrealized_pnl for p in positions]
    fig.add_trace(
        go.Bar(
            x=labels,
            y=pnl_values,
            marker_color=colors
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=300,
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_trade_history(trades: List[Trade], limit: int = 20) -> None:
    """Render trade history table."""
    if not trades:
        st.info("📭 No trades yet")
        return
    
    # Limit trades
    trades_to_show = trades[:limit]
    
    data = []
    for trade in trades_to_show:
        pnl = "N/A"  # Would calculate from pair trades
        data.append({
            "Time": trade.executed_at.strftime("%H:%M:%S"),
            "Pair": trade.symbol,
            "Side": "🟢 BUY" if trade.side.value == "buy" else "🔴 SELL",
            "Amount": f"{trade.amount:.4f}",
            "Price": f"${trade.price:,.2f}",
            "Fee": f"${trade.fee:.2f}",
            "Strategy": trade.strategy or "Manual"
        })
    
    st.dataframe(data, use_container_width=True, hide_index=True)


def render_open_orders(orders, cancel_func=None) -> None:
    """Render open orders table."""
    if not orders:
        st.info("📭 No open orders")
        return
    
    for order in orders:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{order['symbol']}**")
                st.caption(f"{order['side'].upper()} • {order['type']}")
            
            with col2:
                st.metric("Amount", f"{order['amount']:.4f}")
            
            with col3:
                st.metric("Price", f"${order.get('price', 0):,.2f}")
            
            with col4:
                st.caption(f"Created {order.get('created_at', 'N/A')}")
            
            with col5:
                if cancel_func and st.button("❌", key=f"cancel_{order['id']}"):
                    cancel_func(order['id'])
                    st.rerun()
        
        st.markdown("---")


def render_position_manager(position: Position) -> None:
    """Render position management actions."""
    st.subheader(f"📊 {position.symbol} Position")
    
    # Current state
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Size", f"{position.amount:.4f}")
    with col2:
        st.metric("Entry", f"${position.entry_price:,.2f}")
    with col3:
        st.metric("Current", f"${position.current_price:,.2f}")
    
    # P&L
    pnl = position.pnl + position.unrealized_pnl
    st.metric(
        "Unrealized P&L",
        f"${pnl:,.2f}",
        delta=f"{position.pnl_pct:+.2f}%",
        delta_color="normal" if position.pnl_pct >= 0 else "inverse"
    )
    
    st.markdown("---")
    
    # Management actions
    st.subheader("⚡ Actions")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("📈 Set Take Profit", use_container_width=True):
            st.info("Take profit configuration coming soon")
    
    with action_col2:
        if st.button("📉 Set Stop Loss", use_container_width=True):
            st.info("Stop loss configuration coming soon")
    
    with action_col3:
        if st.button("🔄 Close Position", use_container_width=True, type="primary"):
            st.info("Position close feature coming soon")
    
    st.markdown("---")
    
    # Position history
    st.subheader("📜 Order History")
    if position.orders:
        for i, order_id in enumerate(position.orders):
            st.text(f"Order: {order_id}")
    else:
        st.caption("No order history available")
