"""
Command Line Interface for Multi-Agent E-commerce System
"""

import os
import sys
import asyncio
from pathlib import Path
import click
import structlog
from typing import Optional

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from .agents.start_agents import main as start_agents_main
from .shared.database import DatabaseManager, create_database_manager
from .shared.models import DatabaseConfig

logger = structlog.get_logger(__name__)


def setup_logging(level: str = "INFO"):
    """Setup structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    import logging
    logging.getLogger().setLevel(getattr(logging, level.upper()))


def load_environment():
    """Load environment configuration."""
    # Try to load from .env file
    env_file = Path(".env")
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        click.echo(f"Environment loaded from {env_file}")
    
    # Set defaults
    os.environ.setdefault("LOG_LEVEL", "INFO")
    os.environ.setdefault("DATABASE_HOST", "localhost")
    os.environ.setdefault("DATABASE_PORT", "5432")
    os.environ.setdefault("DATABASE_NAME", "multi_agent_ecommerce")
    os.environ.setdefault("DATABASE_USER", "postgres")


def get_database_config() -> DatabaseConfig:
    """Get database configuration from environment."""
    return DatabaseConfig(
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=int(os.getenv("DATABASE_PORT", "5432")),
        database=os.getenv("DATABASE_NAME", "multi_agent_ecommerce"),
        username=os.getenv("DATABASE_USER", "postgres"),
        password=os.getenv("DATABASE_PASSWORD", ""),
        pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    )


@click.group()
@click.option('--log-level', '-l', default='INFO', help='Logging level')
@click.pass_context
def cli(ctx, log_level):
    """Multi-Agent E-commerce System CLI."""
    ctx.ensure_object(dict)
    ctx.obj['log_level'] = log_level
    
    setup_logging(log_level)
    load_environment()


@cli.command()
@click.option('--agents', multiple=True, help='Specific agents to start')
@click.pass_context
def start(ctx, agents):
    """Start the multi-agent system."""
    click.echo("Starting Multi-Agent E-commerce System...")
    
    try:
        # Start the agents
        if agents:
            click.echo(f"Starting specific agents: {', '.join(agents)}")
            start_agents_main(agents=list(agents))
        else:
            click.echo("Starting all agents...")
            start_agents_main()
    except KeyboardInterrupt:
        click.echo("Received keyboard interrupt, shutting down...")
    except Exception as e:
        click.echo(f"Error starting system: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Check system status."""
    click.echo("Multi-Agent E-commerce System Status")
    click.echo("=" * 40)
    
    # Check environment
    click.echo(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    click.echo(f"Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
    
    # Check database config
    db_config = get_database_config()
    click.echo(f"Database: {db_config.host}:{db_config.port}/{db_config.database}")
    click.echo(f"Database User: {db_config.username}")
    
    # Check other services
    click.echo(f"Kafka: {os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')}")
    click.echo(f"Redis: {os.getenv('REDIS_URL', 'redis://localhost:6379/0')}")


@cli.command()
@click.pass_context
def init_db(ctx):
    """Initialize database tables."""
    click.echo("Initializing database...")
    
    async def init_database():
        try:
            db_config = get_database_config()
            db_manager = await create_database_manager(db_config)
            
            # Create tables
            await db_manager.create_tables()
            click.echo("Database tables created successfully")
            
            await db_manager.close()
            
        except Exception as e:
            click.echo(f"Database initialization failed: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(init_database())


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health."""
    click.echo("Multi-Agent E-commerce System Health Check")
    click.echo("=" * 50)
    
    # Basic health checks
    checks = [
        ("Python Environment", lambda: True),
        ("Configuration", check_configuration),
        ("Database Connection", check_database_connection),
    ]
    
    all_healthy = True
    
    for check_name, check_func in checks:
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = asyncio.run(check_func())
            else:
                result = check_func()
            
            status = "✓ PASS" if result else "✗ FAIL"
            click.echo(f"{check_name:.<30} {status}")
            
            if not result:
                all_healthy = False
                
        except Exception as e:
            click.echo(f"{check_name:.<30} ✗ ERROR: {str(e)}")
            all_healthy = False
    
    click.echo("\n" + "=" * 50)
    overall_status = "HEALTHY" if all_healthy else "ISSUES DETECTED"
    click.echo(f"Overall Status: {overall_status}")


def check_configuration():
    """Check basic configuration."""
    required_vars = ["DATABASE_HOST", "DATABASE_NAME", "DATABASE_USER"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        click.echo(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    return True


async def check_database_connection():
    """Check database connection."""
    try:
        db_config = get_database_config()
        db_manager = await create_database_manager(db_config)
        
        # Test connection
        await db_manager.test_connection()
        await db_manager.close()
        
        return True
        
    except Exception as e:
        click.echo(f"Database connection failed: {e}")
        return False


@cli.command()
@click.option('--format', 'output_format', default='table', help='Output format (table, json, yaml)')
@click.pass_context
def config(ctx, output_format):
    """Show current configuration."""
    config_data = {
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'database': {
            'host': os.getenv('DATABASE_HOST', 'localhost'),
            'port': int(os.getenv('DATABASE_PORT', '5432')),
            'database': os.getenv('DATABASE_NAME', 'multi_agent_ecommerce'),
            'user': os.getenv('DATABASE_USER', 'postgres')
        },
        'kafka': {
            'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        },
        'redis': {
            'url': os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        }
    }
    
    if output_format == 'json':
        import json
        click.echo(json.dumps(config_data, indent=2))
    elif output_format == 'yaml':
        try:
            import yaml
            click.echo(yaml.dump(config_data, default_flow_style=False))
        except ImportError:
            click.echo("PyYAML not installed, falling back to table format")
            output_format = 'table'
    
    if output_format == 'table':
        click.echo("Current Configuration:")
        click.echo("=" * 50)
        for section, values in config_data.items():
            click.echo(f"\n{section.upper()}:")
            if isinstance(values, dict):
                for key, value in values.items():
                    click.echo(f"  {key}: {value}")
            else:
                click.echo(f"  {values}")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
