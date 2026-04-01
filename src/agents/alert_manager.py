"""
Alert Manager
Real-time notifications via Telegram, Email, and Push.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import yaml
import requests

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts."""
    TRADE = "trade"
    PNL = "pnl"
    POSITION = "position"
    SYSTEM = "system"
    RISK = "risk"
    AGENT = "agent"


@dataclass
class Alert:
    """Represents an alert/notification."""
    alert_id: str
    alert_type: AlertType
    level: AlertLevel
    title: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    sent: bool = False
    read: bool = False


class TelegramNotifier:
    """Send alerts via Telegram bot."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Send message to Telegram."""
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send formatted alert to Telegram."""
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.SUCCESS: "✅",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        emoji = level_emoji.get(alert.level, "ℹ️")
        
        message = f"""
{emoji} *KEOTrading Alert*

*{alert.title}*
{alert.message}

📅 {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}

#keotrading #{alert.alert_type.value}
"""
        return await self.send(message)


class EmailNotifier:
    """Send alerts via email."""
    
    def __init__(self, smtp_server: str, smtp_port: int, 
                 from_addr: str, to_addrs: List[str],
                 username: str = None, password: str = None):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.username = username
        self.password = password
    
    async def send(self, subject: str, body: str) -> bool:
        """Send email."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addrs)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.username and self.password:
                    server.starttls()
                    server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send formatted alert as email."""
        subject = f"[KEOTrading] {alert.level.value.upper()}: {alert.title}"
        
        body = f"""
        <h2>KEOTrading Alert</h2>
        <p><strong>{alert.title}</strong></p>
        <p>{alert.message}</p>
        <hr>
        <p><small>Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        """
        
        return await self.send(subject, body)


class PushNotifier:
    """Send push notifications via various services."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    async def send(self, title: str, message: str) -> bool:
        """Send push notification."""
        # Support for various push services
        if self.config.get('service') == 'pushover':
            return await self._send_pushover(title, message)
        elif self.config.get('service') == 'ntfy':
            return await self._send_ntfy(title, message)
        else:
            logger.warning("No push service configured")
            return False
    
    async def _send_pushover(self, title: str, message: str) -> bool:
        """Send via Pushover."""
        try:
            response = requests.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": self.config.get('app_token'),
                    "user": self.config.get('user_key'),
                    "title": title,
                    "message": message
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Pushover error: {e}")
            return False
    
    async def _send_ntfy(self, title: str, message: str) -> bool:
        """Send via ntfy."""
        try:
            response = requests.post(
                self.config.get('ntfy_url', 'https://ntfy.sh/keotrading'),
                data=message.encode('utf-8'),
                headers={
                    "Title": title,
                    "Tags": "trading"
                },
                timeout=10
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"ntfy error: {e}")
            return False
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert as push notification."""
        return await self.send(alert.title, alert.message)


class AlertManager:
    """
    Central alert management system.
    Routes alerts to configured notification channels.
    """
    
    def __init__(self, config_path: str = "configs/alerts.yaml"):
        self.config_path = config_path
        self.alerts: List[Alert] = []
        self.alert_id_counter = 0
        
        # Notifiers
        self.telegram: Optional[TelegramNotifier] = None
        self.email: Optional[EmailNotifier] = None
        self.push: Optional[PushNotifier] = None
        
        # Alert rules
        self.rules: List[AlertRule] = []
        
        self._load_config()
    
    def _load_config(self):
        """Load alert configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Telegram
            if config.get('telegram', {}).get('enabled'):
                self.telegram = TelegramNotifier(
                    bot_token=config['telegram']['bot_token'],
                    chat_id=config['telegram']['chat_id']
                )
            
            # Email
            if config.get('email', {}).get('enabled'):
                self.email = EmailNotifier(
                    smtp_server=config['email']['smtp_server'],
                    smtp_port=config['email']['smtp_port'],
                    from_addr=config['email']['from_addr'],
                    to_addrs=config['email']['to_addrs'],
                    username=config['email'].get('username'),
                    password=config['email'].get('password')
                )
            
            # Push
            if config.get('push', {}).get('enabled'):
                self.push = PushNotifier(config['push'])
            
            # Alert rules
            for rule in config.get('rules', []):
                self.rules.append(AlertRule(
                    name=rule['name'],
                    alert_type=AlertType(rule['type']),
                    condition=rule['condition'],
                    level=AlertLevel(rule['level']),
                    cooldown_seconds=rule.get('cooldown', 300)
                ))
                
        except FileNotFoundError:
            logger.warning(f"Alert config not found: {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading alert config: {e}")
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        self.alert_id_counter += 1
        return f"ALT-{datetime.now().strftime('%Y%m%d')}-{self.alert_id_counter:06d}"
    
    async def send_alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        title: str,
        message: str,
        data: Dict[str, Any] = None,
        notify: bool = True
    ) -> Alert:
        """Create and send an alert."""
        alert = Alert(
            alert_id=self._generate_alert_id(),
            alert_type=alert_type,
            level=level,
            title=title,
            message=message,
            data=data or {}
        )
        
        self.alerts.append(alert)
        
        if notify:
            await self._notify(alert)
        
        return alert
    
    async def _notify(self, alert: Alert):
        """Send alert to all configured channels."""
        tasks = []
        
        if self.telegram:
            tasks.append(self.telegram.send_alert(alert))
        if self.email:
            tasks.append(self.email.send_alert(alert))
        if self.push:
            tasks.append(self.push.send_alert(alert))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            alert.sent = any(r is True for r in results)
    
    async def alert_trade(self, trade_data: Dict[str, Any]):
        """Send trade alert."""
        side = trade_data.get('side', 'unknown').upper()
        emoji = "🟢" if side == "BUY" else "🔴"
        
        await self.send_alert(
            alert_type=AlertType.TRADE,
            level=AlertLevel.SUCCESS if side == "BUY" else AlertLevel.INFO,
            title=f"Trade Executed: {side}",
            message=f"{emoji} {trade_data.get('amount')} {trade_data.get('symbol')} @ {trade_data.get('price')}",
            data=trade_data
        )
    
    async def alert_pnl(self, pnl_data: Dict[str, Any]):
        """Send P&L alert."""
        pnl = pnl_data.get('pnl', 0)
        level = AlertLevel.CRITICAL if pnl < -0.05 else AlertLevel.WARNING if pnl < 0 else AlertLevel.SUCCESS
        
        await self.send_alert(
            alert_type=AlertType.PNL,
            level=level,
            title=f"P&L Alert: {pnl:+.2%}",
            message=f"Daily P&L: ${pnl_data.get('daily', 0):+.2f} | Total: ${pnl_data.get('total', 0):+.2f}",
            data=pnl_data
        )
    
    async def alert_risk(self, risk_data: Dict[str, Any]):
        """Send risk alert."""
        await self.send_alert(
            alert_type=AlertType.RISK,
            level=AlertLevel.ERROR,
            title=f"Risk Alert: {risk_data.get('type')}",
            message=risk_data.get('message', 'Risk limit breached'),
            data=risk_data
        )
    
    async def alert_agent(self, agent_data: Dict[str, Any]):
        """Send agent status alert."""
        status = agent_data.get('status', 'unknown')
        
        if status == 'error':
            level = AlertLevel.ERROR
        elif status == 'paused':
            level = AlertLevel.WARNING
        else:
            level = AlertLevel.INFO
        
        await self.send_alert(
            alert_type=AlertType.AGENT,
            level=level,
            title=f"Agent Status: {agent_data.get('name', 'Unknown')}",
            message=f"Status changed to *{status.upper()}*",
            data=agent_data
        )
    
    async def alert_system(self, message: str, level: AlertLevel = AlertLevel.INFO):
        """Send system alert."""
        await self.send_alert(
            alert_type=AlertType.SYSTEM,
            level=level,
            title="System Alert",
            message=message
        )
    
    def get_alerts(self, limit: int = 50, unread_only: bool = False) -> List[Alert]:
        """Get recent alerts."""
        alerts = sorted(self.alerts, key=lambda a: a.created_at, reverse=True)
        
        if unread_only:
            alerts = [a for a in alerts if not a.read]
        
        return alerts[:limit]
    
    def mark_read(self, alert_id: str) -> bool:
        """Mark alert as read."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.read = True
                return True
        return False
    
    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts.clear()


@dataclass
class AlertRule:
    """Rule for automatic alert generation."""
    name: str
    alert_type: AlertType
    condition: str  # e.g., "pnl < -0.05"
    level: AlertLevel
    cooldown_seconds: int = 300
    
    # Internal state
    last_triggered: Optional[datetime] = None
    
    def should_fire(self) -> bool:
        """Check if rule should fire (respecting cooldown)."""
        if self.last_triggered is None:
            return True
        
        elapsed = (datetime.now() - self.last_triggered).total_seconds()
        return elapsed >= self.cooldown_seconds
    
    def trigger(self):
        """Mark rule as triggered."""
        self.last_triggered = datetime.now()
