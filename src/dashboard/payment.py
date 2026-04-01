"""
Payment / Deposit Manager
Handles credit card deposits via MoonPay, Ramp, Mercuryo, and direct exchange transfers.
"""

import asyncio
import logging
import hashlib
import hmac
import json
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)


@dataclass
class DepositRequest:
    """A deposit request."""
    id: str
    amount: float
    currency: str  # USD, EUR, etc.
    crypto_currency: str  # BTC, ETH, USDT, etc.
    provider: str  # moonpay, ramp, mercuryo, exchange
    status: str  # pending, processing, completed, failed
    payment_url: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class PaymentProvider:
    """Base class for payment providers."""
    
    def __init__(self, api_key: str, api_secret: str = None, testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
    
    async def create_deposit(self, amount: float, currency: str, 
                            crypto_currency: str, wallet_address: str,
                            email: str = None) -> DepositRequest:
        """Create a deposit request."""
        raise NotImplementedError
    
    async def get_deposit_status(self, deposit_id: str) -> DepositRequest:
        """Check deposit status."""
        raise NotImplementedError
    
    def get_payment_url(self, deposit: DepositRequest) -> Optional[str]:
        """Get the payment URL for a deposit."""
        raise NotImplementedError


class MoonPayProvider(PaymentProvider):
    """MoonPay credit card integration."""
    
    BASE_URL_TEST = "https://api-sandbox.moonpay.com"
    BASE_URL_PROD = "https://api.moonpay.com"
    
    def __init__(self, api_key: str, api_secret: str = None, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        self.base_url = self.BASE_URL_TEST if testnet else self.BASE_URL_PROD
    
    def _generate_signature(self, message: str) -> str:
        """Generate HMAC signature for API requests."""
        if not self.api_secret:
            return ""
        return hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def create_deposit(self, amount: float, currency: str,
                           crypto_currency: str, wallet_address: str,
                           email: str = None) -> DepositRequest:
        """Create a MoonPay deposit."""
        import uuid
        
        deposit_id = f"mp_{uuid.uuid4().hex[:12]}"
        
        # MoonPay API parameters
        params = {
            'apiKey': self.api_key,
            'currency': crypto_currency.lower(),
            'amount': str(amount),
            'fiatCurrency': currency.upper(),
            'walletAddress': wallet_address,
            'redirectUrl': 'keo://deposit/complete',
            'showWalletAddressForm': 'false',
        }
        
        if email:
            params['email'] = email
        
        # Build payment URL
        payment_url = f"{self.base_url}/v3/currency_orders/buy?" + urllib.parse.urlencode(params)
        
        return DepositRequest(
            id=deposit_id,
            amount=amount,
            currency=currency,
            crypto_currency=crypto_currency,
            provider="moonpay",
            status="pending",
            payment_url=payment_url,
            created_at=datetime.now()
        )
    
    async def get_deposit_status(self, deposit_id: str) -> Optional[DepositRequest]:
        """Check MoonPay deposit status via API."""
        try:
            import requests
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/v3/currency_orders/{deposit_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return DepositRequest(
                    id=deposit_id,
                    amount=float(data.get('baseCurrencyAmount', 0)),
                    currency=data.get('fiatCurrencyCode', 'USD'),
                    crypto_currency=data.get('cryptoCurrencyCode', 'BTC'),
                    provider="moonpay",
                    status=data.get('status', 'pending'),
                    created_at=datetime.now()
                )
        except Exception as e:
            logger.error(f"MoonPay status check failed: {e}")
        
        return None
    
    def get_payment_url(self, deposit: DepositRequest) -> Optional[str]:
        return deposit.payment_url


class RampProvider(PaymentProvider):
    """Ramp Network credit card integration."""
    
    BASE_URL_TEST = "https://api-qa.ramp.network"
    BASE_URL_PROD = "https://api.ramp.network"
    
    def __init__(self, api_key: str, api_secret: str = None, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        self.base_url = self.BASE_URL_TEST if testnet else self.BASE_URL_PROD
    
    async def create_deposit(self, amount: float, currency: str,
                           crypto_currency: str, wallet_address: str,
                           email: str = None) -> DepositRequest:
        """Create a Ramp deposit."""
        import uuid
        
        deposit_id = f"ramp_{uuid.uuid4().hex[:12]}"
        
        # Ramp URL construction
        params = {
            'apiKey': self.api_key,
            'swapAsset': f'SYM:{crypto_currency.upper()}_{currency.upper()}' if currency != 'USD' else f'SYM:{crypto_currency.upper()}_USD',
            'fiatValue': str(amount),
            'fiatCurrency': currency.upper(),
            'userAddress': wallet_address,
            'hostApiKey': self.api_key,
            'hostLogoUrl': 'https://keo.trading/logo.png',
            'hostAppName': 'KEOTrading',
            'redirectUrl': 'keo://deposit/complete',
        }
        
        payment_url = f"{self.base_url}/?" + urllib.parse.urlencode(params)
        
        return DepositRequest(
            id=deposit_id,
            amount=amount,
            currency=currency,
            crypto_currency=crypto_currency,
            provider="ramp",
            status="pending",
            payment_url=payment_url,
            created_at=datetime.now()
        )
    
    async def get_deposit_status(self, deposit_id: str) -> Optional[DepositRequest]:
        """Check Ramp deposit status."""
        # Ramp provides webhook-based status updates
        # For now, return pending
        return DepositRequest(
            id=deposit_id,
            amount=0,
            currency="USD",
            crypto_currency="USDT",
            provider="ramp",
            status="pending",
            created_at=datetime.now()
        )
    
    def get_payment_url(self, deposit: DepositRequest) -> Optional[str]:
        return deposit.payment_url


class MercuryoProvider(PaymentProvider):
    """Mercuryo credit card integration."""
    
    BASE_URL = "https://api.mercuryo.io"
    
    async def create_deposit(self, amount: float, currency: str,
                           crypto_currency: str, wallet_address: str,
                           email: str = None) -> DepositRequest:
        """Create a Mercuryo deposit."""
        import uuid
        
        deposit_id = f"my_{uuid.uuid4().hex[:12]}"
        
        params = {
            'type': 'buy',
            'currency': crypto_currency.upper(),
            'amount': str(amount),
            'fiat_currency': currency.upper(),
            'wallet_address': wallet_address,
            'redirect_url': 'keo://deposit/complete',
        }
        
        payment_url = f"{self.BASE_URL}/v1/widget?" + urllib.parse.urlencode(params)
        
        return DepositRequest(
            id=deposit_id,
            amount=amount,
            currency=currency,
            crypto_currency=crypto_currency,
            provider="mercuryo",
            status="pending",
            payment_url=payment_url,
            created_at=datetime.now()
        )
    
    async def get_deposit_status(self, deposit_id: str) -> Optional[DepositRequest]:
        return None
    
    def get_payment_url(self, deposit: DepositRequest) -> Optional[str]:
        return deposit.payment_url


class ExchangeDirectTransfer:
    """Handles direct deposits to exchanges (manual transfer instructions)."""
    
    @staticmethod
    def get_deposit_instructions(exchange_id: str, currency: str) -> Dict[str, Any]:
        """Get deposit instructions for an exchange."""
        
        instructions = {
            "binance": {
                "name": "Binance",
                "url": "https://www.binance.com/en/my/wallet/deposit",
                "steps": [
                    "1. Log in to your Binance account",
                    "2. Go to Wallet > Deposit",
                    "3. Select the cryptocurrency (e.g., USDT)",
                    "4. Choose 'Credit/Debit Card' as payment method",
                    "5. Enter amount and complete payment",
                    "6. Funds will be credited to your spot wallet"
                ],
                "min_deposit": {"USDT": 10, "BTC": 0.001, "ETH": 0.01},
                "fees": "1-3% depending on card and amount"
            },
            "kraken": {
                "name": "Kraken",
                "url": "https://www.kraken.com/u/funding/deposit",
                "steps": [
                    "1. Log in to your Kraken account",
                    "2. Go to Funding > Deposit",
                    "3. Select cryptocurrency",
                    "4. Click 'Buy Crypto with Card' or use card deposit option",
                    "5. Complete verification if prompted"
                ],
                "min_deposit": {"USDT": 10, "BTC": 0.001, "ETH": 0.01},
                "fees": "0.5-2.5% + network fee"
            },
            "bybit": {
                "name": "Bybit",
                "url": "https://www.bybit.com/en/my/assets/deposit",
                "steps": [
                    "1. Log in to your Bybit account",
                    "2. Go to Assets > Deposit",
                    "3. Select 'Buy Crypto' option",
                    "4. Choose credit card payment",
                    "5. Enter amount and complete purchase"
                ],
                "min_deposit": {"USiquet": 10, "BTC": 0.001, "ETH": 0.01},
                "fees": "2-3.5% depending on region"
            },
            "coinbase": {
                "name": "Coinbase",
                "url": "https://www.coinbase.com/buy",
                "steps": [
                    "1. Log in to your Coinbase account",
                    "2. Click 'Buy' button",
                    "3. Select cryptocurrency",
                    "4. Enter amount and select card",
                    "5. Confirm purchase"
                ],
                "min_deposit": {"USDT": 10, "BTC": 0.001, "ETH": 0.01},
                "fees": "Coinbase fee (1.49-3.99%) + network fee"
            }
        }
        
        return instructions.get(exchange_id, {
            "name": exchange_id.title(),
            "url": "",
            "steps": ["Instructions not available"],
            "min_deposit": {},
            "fees": "Varies"
        })


class PaymentManager:
    """Manages all payment providers and deposits."""
    
    def __init__(self, config_path: str = "configs/exchanges.yaml"):
        self.config_path = config_path
        self.providers: Dict[str, PaymentProvider] = {}
        self.deposits: Dict[str, DepositRequest] = {}
        self._load_config()
    
    def _load_config(self):
        """Load payment provider configuration."""
        import yaml
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            payment_config = config.get('payment', {})
            
            # Initialize MoonPay
            moonpay = payment_config.get('moonpay', {})
            if moonpay.get('enabled') and moonpay.get('api_key'):
                self.providers['moonpay'] = MoonPayProvider(
                    api_key=moonpay['api_key'],
                    api_secret=moonpay.get('api_secret'),
                    testnet=moonpay.get('testnet', False)
                )
                logger.info("MoonPay provider initialized")
            
            # Initialize Ramp
            ramp = payment_config.get('ramp', {})
            if ramp.get('enabled') and ramp.get('api_key'):
                self.providers['ramp'] = RampProvider(
                    api_key=ramp['api_key'],
                    api_secret=ramp.get('api_secret'),
                    testnet=ramp.get('testnet', False)
                )
                logger.info("Ramp provider initialized")
            
            # Initialize Mercuryo
            mercuryo = payment_config.get('mercuryo', {})
            if mercuryo.get('enabled') and mercuryo.get('api_key'):
                self.providers['mercuryo'] = MercuryoProvider(
                    api_key=mercuryo['api_key'],
                    api_secret=mercuryo.get('api_secret')
                )
                logger.info("Mercuryo provider initialized")
                
        except Exception as e:
            logger.warning(f"Could not load payment config: {e}")
    
    async def create_deposit(self, amount: float, currency: str = "USD",
                            crypto_currency: str = "USDT",
                            provider: str = "moonpay",
                            wallet_address: str = None,
                            email: str = None) -> DepositRequest:
        """Create a new deposit request."""
        
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not available. Available: {list(self.providers.keys())}")
        
        if not wallet_address:
            # Generate a deposit address placeholder
            # User should update this with their actual wallet
            wallet_address = "PLEASE_SET_WALLET_ADDRESS"
        
        provider_obj = self.providers[provider]
        deposit = await provider_obj.create_deposit(
            amount=amount,
            currency=currency,
            crypto_currency=crypto_currency,
            wallet_address=wallet_address,
            email=email
        )
        
        self.deposits[deposit.id] = deposit
        return deposit
    
    async def get_deposit(self, deposit_id: str) -> Optional[DepositRequest]:
        """Get deposit by ID."""
        deposit = self.deposits.get(deposit_id)
        
        if deposit and deposit.provider in self.providers:
            updated = await self.providers[deposit.provider].get_deposit_status(deposit_id)
            if updated:
                self.deposits[deposit_id] = updated
                return updated
        
        return deposit
    
    def get_all_deposits(self) -> list:
        """Get all deposits."""
        return list(self.deposits.values())
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of payment providers."""
        return {name: True for name in self.providers.keys()}


def get_payment_manager() -> PaymentManager:
    """Get or create payment manager singleton."""
    import threading
    if not hasattr(get_payment_manager, '_instance'):
        get_payment_manager._instance = PaymentManager()
    return get_payment_manager._instance
