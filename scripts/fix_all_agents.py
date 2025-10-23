"""
Script to automatically fix all crashing agents with enhanced database retry logic.

This script adds robust database initialization with retry logic to all agents.
"""

import re
from pathlib import Path

# Agents that need fixing (excluding the 5 already working)
AGENTS_TO_FIX = [
    "agents/transport_agent_production.py",
    "agents/marketplace_connector_agent_production.py",
    "agents/customer_agent_enhanced.py",
    "agents/after_sales_agent.py",
    "agents/document_generation_agent.py",
    "agents/quality_control_agent.py",
    "agents/backoffice_agent.py",
    "agents/knowledge_management_agent.py",
    "agents/fraud_detection_agent.py",
    "agents/risk_anomaly_detection_agent.py",
]

# Enhanced initialization code template
ENHANCED_INIT_TEMPLATE = '''        # Initialize database with robust retry logic
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                # Try to get global database manager
                try:
                    from shared.database_manager import get_database_manager
                    self.db_manager = get_database_manager()
                    self.logger.info("Using global database manager")
                except (RuntimeError, ImportError):
                    # Create enhanced database manager with retry logic
                    from shared.models import DatabaseConfig
                    from shared.database_manager import EnhancedDatabaseManager
                    db_config = DatabaseConfig()
                    self.db_manager = EnhancedDatabaseManager(db_config)
                    await self.db_manager.initialize(max_retries=5)
                    self.logger.info("Created new enhanced database manager")
                
                self.logger.info("Database initialization successful", attempt=attempt)
                break
                
            except Exception as e:
                self.logger.warning(
                    "Database initialization failed",
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(e)
                )
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Failed to initialize database after all retries")
                    raise'''


def analyze_agent_init(file_path: Path) -> dict:
    """Analyze agent initialization code"""
    content = file_path.read_text()
    
    # Find initialize method
    init_pattern = r'async def initialize\(self[^)]*\):(.*?)(?=\n    async def |\n    def |\Z)'
    match = re.search(init_pattern, content, re.DOTALL)
    
    if not match:
        return {"has_init": False, "content": content}
    
    init_code = match.group(1)
    
    # Check if it already has enhanced retry logic
    has_retry = "max_retries" in init_code and "EnhancedDatabaseManager" in init_code
    
    # Check if it has database initialization
    has_db_init = "db_manager" in init_code or "DatabaseManager" in init_code
    
    return {
        "has_init": True,
        "has_retry": has_retry,
        "has_db_init": has_db_init,
        "init_code": init_code,
        "content": content,
        "init_match": match
    }


def main():
    """Fix all agents"""
    project_root = Path("/home/ubuntu/Multi-agent-AI-Ecommerce")
    
    print("=" * 80)
    print("AGENT FIX ANALYSIS")
    print("=" * 80)
    
    for agent_file in AGENTS_TO_FIX:
        agent_path = project_root / agent_file
        
        if not agent_path.exists():
            print(f"\n❌ {agent_file}: FILE NOT FOUND")
            continue
        
        print(f"\n📝 Analyzing: {agent_file}")
        
        analysis = analyze_agent_init(agent_path)
        
        if not analysis["has_init"]:
            print(f"   ⚠️  No initialize() method found")
            continue
        
        if analysis["has_retry"]:
            print(f"   ✅ Already has enhanced retry logic")
            continue
        
        if not analysis["has_db_init"]:
            print(f"   ℹ️  No database initialization found (may not need DB)")
            continue
        
        print(f"   🔧 Needs fixing - has DB init but no retry logic")
        print(f"   📊 Init code length: {len(analysis['init_code'])} chars")


if __name__ == "__main__":
    main()

