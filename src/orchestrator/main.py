"""
KEOTrading Orchestrator
Main entry point for the multi-agent trading system
"""

import asyncio
import logging
import signal
from typing import Dict, Any

from orchestrator.agent_manager import AgentManager
from orchestrator.communicator import Communicator
from orchestrator.risk_enforcer import RiskEnforcer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KEOTradingOrchestrator:
    """Main orchestrator for all 50 trading agents"""
    
    def __init__(self, config_path: str = "configs/"):
        self.config_path = config_path
        self.running = False
        
        # Core components
        self.communicator = Communicator()
        self.risk_enforcer = RiskEnforcer(self.communicator)
        self.agent_manager = AgentManager(
            self.communicator,
            self.risk_enforcer,
            self.config_path
        )
        
        logger.info("KEOTrading Orchestrator initialized")
    
    async def start(self):
        """Start all agents and systems"""
        logger.info("🚀 Starting KEOTrading System...")
        
        # Initialize communication layer
        await self.communicator.connect()
        
        # Load and start all agents
        await self.agent_manager.load_agents()
        await self.agent_manager.start_all()
        
        self.running = True
        logger.info(f"✅ System running with {self.agent_manager.agent_count} agents")
        
        # Main loop
        await self._run_main_loop()
    
    async def _run_main_loop(self):
        """Main control loop"""
        while self.running:
            try:
                # Check agent health
                health_report = await self.agent_manager.check_health()
                
                # Process any pending commands
                await self._process_commands()
                
                # Wait before next iteration
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await self._handle_error(e)
    
    async def _process_commands(self):
        """Process external commands"""
        # TODO: Implement command queue processing
        pass
    
    async def _handle_error(self, error: Exception):
        """Handle system errors"""
        logger.error(f"Handling error: {error}")
        # TODO: Implement error recovery
    
    async def stop(self):
        """Gracefully shutdown all agents"""
        logger.info("🛑 Shutting down KEOTrading...")
        self.running = False
        
        # Stop all agents gracefully
        await self.agent_manager.stop_all()
        
        # Close connections
        await self.communicator.disconnect()
        
        logger.info("✅ Shutdown complete")
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        asyncio.create_task(self.stop())


async def main():
    """Entry point"""
    orchestrator = KEOTradingOrchestrator()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, orchestrator.handle_signal)
    signal.signal(signal.SIGTERM, orchestrator.handle_signal)
    
    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        pass
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
