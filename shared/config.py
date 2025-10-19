"""
Configuration management with validation using Pydantic.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class KafkaConfig(BaseModel):
    """Kafka configuration."""
    bootstrap_servers: str = Field(default="localhost:9092", description="Kafka bootstrap servers")
    group_id_prefix: str = Field(default="multi_agent", description="Consumer group ID prefix")
    auto_offset_reset: str = Field(default="latest", description="Auto offset reset policy")
    enable_auto_commit: bool = Field(default=True, description="Enable auto commit")
    
    @validator('bootstrap_servers')
    def validate_bootstrap_servers(cls, v):
        """Validate bootstrap servers format."""
        if not v or ':' not in v:
            raise ValueError('Bootstrap servers must be in format host:port')
        return v


class DatabaseConfig(BaseModel):
    """Database configuration."""
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, ge=1, le=65535, description="Database port")
    database: str = Field(..., min_length=1, description="Database name")
    username: str = Field(..., min_length=1, description="Database username")
    password: str = Field(..., min_length=1, description="Database password")
    pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=20, ge=0, le=100, description="Max overflow connections")
    echo: bool = Field(default=False, description="Echo SQL statements")
    
    @property
    def url(self) -> str:
        """Generate database URL."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @validator('port')
    def validate_port(cls, v):
        """Validate port is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class RedisConfig(BaseModel):
    """Redis configuration."""
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    password: Optional[str] = Field(default=None, description="Redis password")
    db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    
    @property
    def url(self) -> str:
        """Generate Redis URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    model: str = Field(default="gpt-3.5-turbo", description="Default model to use")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=500, ge=1, le=4000, description="Max tokens per request")
    
    @validator('api_key')
    def validate_api_key(cls, v):
        """Validate API key format."""
        if v and not v.startswith('sk-'):
            raise ValueError('OpenAI API key must start with sk-')
        return v


class AgentConfig(BaseModel):
    """Individual agent configuration."""
    agent_id: str = Field(..., min_length=1, description="Unique agent identifier")
    log_level: str = Field(default="INFO", description="Logging level")
    health_check_interval: int = Field(default=60, ge=10, description="Health check interval in seconds")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    retry_delay: int = Field(default=5, ge=1, description="Retry delay in seconds")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()


class SystemConfig(BaseSettings):
    """System-wide configuration loaded from environment variables."""
    
    # Environment
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Database
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    database_port: int = Field(default=5432, env="DATABASE_PORT")
    database_name: str = Field(default="multi_agent_ecommerce", env="DATABASE_NAME")
    database_user: str = Field(default="postgres", env="DATABASE_USER")
    database_password: str = Field(default="", env="DATABASE_PASSWORD")
    
    # Kafka
    kafka_bootstrap_servers: str = Field(default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    
    # Redis
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration."""
        return DatabaseConfig(
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
            username=self.database_user,
            password=self.database_password
        )
    
    def get_kafka_config(self) -> KafkaConfig:
        """Get Kafka configuration."""
        return KafkaConfig(
            bootstrap_servers=self.kafka_bootstrap_servers
        )
    
    def get_redis_config(self) -> RedisConfig:
        """Get Redis configuration."""
        return RedisConfig(
            host=self.redis_host,
            port=self.redis_port,
            password=self.redis_password
        )
    
    def get_openai_config(self) -> OpenAIConfig:
        """Get OpenAI configuration."""
        return OpenAIConfig(
            api_key=self.openai_api_key
        )


# Global configuration instance
_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """Get or create global configuration instance."""
    global _config
    if _config is None:
        _config = SystemConfig()
    return _config


def reload_config() -> SystemConfig:
    """Reload configuration from environment."""
    global _config
    _config = SystemConfig()
    return _config

