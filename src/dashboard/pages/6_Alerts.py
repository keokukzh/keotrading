"""
KEOTrading Dashboard - Alerts Page
Real-time notifications, alert history, and alert rule management.
"""

from __future__ import annotations

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# Mock alert data
def get_mock_alerts() -> List[Dict[str, Any]]:
    """Generate mock alerts for demo."""
    now = datetime.now()
    return [
        {
            "id": "ALT-20260401-001",
            "type": "trade",
            "level": "success",
            "title": "Buy Order Executed",
            "message": "Purchased 0.05 BTC @ $64,200 on Binance",
            "time": now - timedelta(minutes=5),
            "read": False
        },
        {
            "id": "ALT-20260401-002",
            "type": "pnl",
            "level": "success",
            "title": "Profit Target Hit",
            "message": "Grid Bot closed position with +$45.20 profit",
            "time": now - timedelta(minutes=15),
            "read": False
        },
        {
            "id": "ALT-20260401-003",
            "type": "agent",
            "level": "warning",
            "title": "Agent Paused",
            "message": "Grid Bot Beta paused due to drawdown limit",
            "time": now - timedelta(minutes=30),
            "read": True
        },
        {
            "id": "ALT-20260401-004",
            "type": "risk",
            "level": "error",
            "title": "Risk Limit Approaching",
            "message": "Daily loss at $850 of $1000 limit (85%)",
            "time": now - timedelta(hours=1),
            "read": True
        },
        {
            "id": "ALT-20260401-005",
            "type": "system",
            "level": "info",
            "title": "System Online",
            "message": "All systems operational. 48/50 agents running.",
            "time": now - timedelta(hours=2),
            "read": True
        },
        {
            "id": "ALT-20260401-006",
            "type": "trade",
            "level": "success",
            "title": "Sell Order Executed",
            "message": "Sold 2.5 ETH @ $3,420 on Binance",
            "time": now - timedelta(hours=3),
            "read": True
        },
        {
            "id": "ALT-20260401-007",
            "type": "pnl",
            "level": "warning",
            "title": "Daily Target Almost Reached",
            "message": "Daily P&L at $980 of $1000 target",
            "time": now - timedelta(hours=4),
            "read": True
        },
        {
            "id": "ALT-20260401-008",
            "type": "agent",
            "level": "info",
            "title": "New Agent Started",
            "message": "LLM Advisor agent started successfully",
            "time": now - timedelta(hours=5),
            "read": True
        },
    ]


def render_alert_icon(level: str) -> str:
    """Get icon for alert level."""
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "critical": "🚨"
    }
    return icons.get(level, "ℹ️")


def render_alert_type_icon(alert_type: str) -> str:
    """Get icon for alert type."""
    icons = {
        "trade": "📈",
        "pnl": "💰",
        "position": "📊",
        "system": "🖥️",
        "risk": "⚠️",
        "agent": "🤖"
    }
    return icons.get(alert_type, "📢")


def render_alerts_page():
    """Render the Alerts page."""
    st.title("🔔 Alerts & Notifications")
    st.markdown("Monitor trading alerts, notifications, and system events.")
    st.markdown("---")
    
    # Alert stats
    alerts = get_mock_alerts()
    unread_count = len([a for a in alerts if not a['read']])
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    with stat_col1:
        st.metric("Total Alerts", len(alerts))
    with stat_col2:
        st.metric("Unread", unread_count, delta=-2 if unread_count < 5 else 0)
    with stat_col3:
        st.metric("Today", len([a for a in alerts if (datetime.now() - a['time']).hours < 24]))
    with stat_col4:
        st.metric("Critical", len([a for a in alerts if a['level'] in ['error', 'critical']]))
    
    st.markdown("---")
    
    # Configuration section
    config_col1, config_col2, config_col3 = st.columns([1, 1, 1])
    
    with config_col1:
        st.subheader("📳 Notification Channels")
        
        telegram_enabled = st.checkbox("Telegram", value=True)
        if telegram_enabled:
            st.text_input("Bot Token", value="123456:ABC-DEF...", type="password")
            st.text_input("Chat ID", value="-100123456789")
        
        email_enabled = st.checkbox("Email", value=False)
        if email_enabled:
            st.text_input("SMTP Server", value="smtp.gmail.com")
            st.text_input("From", value="alerts@keotrading.com")
            st.text_input("To", value="eddy@example.com")
    
    with config_col2:
        st.subheader("⚙️ Alert Rules")
        
        alert_rules = [
            {"name": "Trade Executed", "enabled": True, "channels": ["Telegram"]},
            {"name": "P&L > 5%", "enabled": True, "channels": ["Telegram", "Email"]},
            {"name": "Risk Limit 80%", "enabled": True, "channels": ["Telegram", "Email"]},
            {"name": "Agent Error", "enabled": True, "channels": ["Telegram"]},
            {"name": "Daily Loss > $500", "enabled": True, "channels": ["Telegram"]},
        ]
        
        for rule in alert_rules:
            enabled = st.checkbox(f"{rule['name']}", value=rule['enabled'])
    
    with config_col3:
        st.subheader("🚨 Critical Alerts")
        
        st.checkbox("Emergency Stop Triggers", value=True)
        st.checkbox("Drawdown > 10%", value=True)
        st.checkbox("All Agents Down", value=True)
        st.checkbox("Exchange Connection Lost", value=True)
        
        st.markdown("---")
        
        if st.button("🧪 Test Notification", use_container_width=True):
            st.success("✅ Test notification sent to Telegram!")
    
    st.markdown("---")
    
    # Filter controls
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1, 1])
    
    with filter_col1:
        filter_type = st.selectbox("Type", ["All", "Trade", "P&L", "Risk", "Agent", "System"])
    
    with filter_col2:
        filter_level = st.selectbox("Level", ["All", "Critical", "Error", "Warning", "Success", "Info"])
    
    with filter_col3:
        filter_status = st.selectbox("Status", ["All", "Unread", "Read"])
    
    with filter_col4:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    st.markdown("---")
    
    # Alert list
    st.subheader("📋 Alert History")
    
    # Filter alerts
    filtered_alerts = alerts
    if filter_type != "All":
        filtered_alerts = [a for a in filtered_alerts if a['type'].lower() == filter_type.lower()]
    if filter_level != "All":
        filtered_alerts = [a for a in filtered_alerts if a['level'].lower() == filter_level.lower()]
    if filter_status == "Unread":
        filtered_alerts = [a for a in filtered_alerts if not a['read']]
    elif filter_status == "Read":
        filtered_alerts = [a for a in filtered_alerts if a['read']]
    
    # Render alerts
    for alert in filtered_alerts:
        with st.container():
            alert_col1, alert_col2 = st.columns([4, 1])
            
            with alert_col1:
                # Alert header
                type_icon = render_alert_type_icon(alert['type'])
                level_icon = render_alert_icon(alert['level'])
                
                if not alert['read']:
                    st.markdown(f"**{type_icon} {alert['title']}** {level_icon} 🔵")
                else:
                    st.markdown(f"**{type_icon} {alert['title']}** {level_icon}")
                
                st.markdown(alert['message'])
                
                # Metadata
                meta_col1, meta_col2, meta_col3 = st.columns([1, 1, 2])
                with meta_col1:
                    st.caption(f"Type: {alert['type'].upper()}")
                with meta_col2:
                    st.caption(f"Level: {alert['level'].upper()}")
                with meta_col3:
                    time_diff = datetime.now() - alert['time']
                    if time_diff < timedelta(minutes=1):
                        time_str = "Just now"
                    elif time_diff < timedelta(hours=1):
                        time_str = f"{int(time_diff.total_seconds() / 60)}m ago"
                    else:
                        time_str = f"{int(time_diff.total_seconds() / 3600)}h ago"
                    st.caption(time_str)
            
            with alert_col2:
                if not alert['read']:
                    if st.button("✓", key=f"read_{alert['id']}"):
                        st.info("Marked as read")
                        st.rerun()
                else:
                    st.write("")
            
            st.markdown("---")
    
    # Mark all as read
    if st.button("✓ Mark All as Read"):
        st.success("All alerts marked as read")
        st.rerun()
    
    # Clear all
    if st.button("🗑️ Clear All Alerts"):
        st.warning("This will delete all alerts. Continue?")
        if st.button("Yes, Delete All"):
            st.info("Alerts cleared")
            st.rerun()


if __name__ == "__main__":
    render_alerts_page()
