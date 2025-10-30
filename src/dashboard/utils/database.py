"""Database utilities for Streamlit dashboard.

This module provides centralized database connection management with:
- Connection pooling
- Session management
- Resource caching
- Connection health checks
"""

import streamlit as st
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@st.cache_resource
def get_engine(db_url: str):
    """Get cached database engine with connection pooling.
    
    Args:
        db_url: SQLAlchemy database URL
        
    Returns:
        SQLAlchemy Engine instance with connection pooling configured
        
    Note:
        This function is cached using @st.cache_resource, so the same engine
        is reused across Streamlit reruns. The cache is keyed by db_url.
    """
    logger.info(f"Creating database engine for: {db_url.split('://')[0]}://***")
    
    # Special handling for SQLite in-memory databases
    if db_url.startswith("sqlite:///:memory:") or db_url == "sqlite://":
        engine = create_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool  # Required for in-memory databases
        )
    else:
        # Production configuration with connection pooling
        engine = create_engine(
            db_url,
            echo=False,
            pool_size=5,              # Number of connections to keep in pool
            max_overflow=10,          # Max connections beyond pool_size
            pool_pre_ping=True,       # Verify connection health before use
            pool_recycle=3600,        # Recycle connections after 1 hour
            pool_timeout=30,          # Timeout waiting for connection
        )
    
    # Add event listener for connection checkout (useful for debugging)
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        logger.debug("Database connection established")
    
    return engine


@st.cache_resource
def get_session_factory(db_url: str):
    """Get cached session factory.
    
    Args:
        db_url: SQLAlchemy database URL
        
    Returns:
        sessionmaker instance bound to cached engine
        
    Note:
        This is cached so the same session factory is reused across reruns.
    """
    engine = get_engine(db_url)
    return sessionmaker(bind=engine, expire_on_commit=False)


class DatabaseManager:
    """Centralized database connection and session management."""
    
    @staticmethod
    def get_session(db_url: str) -> Session:
        """Get a new database session.
        
        Args:
            db_url: SQLAlchemy database URL
            
        Returns:
            SQLAlchemy Session instance
            
        Example:
            session = DatabaseManager.get_session(db_url)
            try:
                # Use session
                vms = session.query(VirtualMachine).all()
            finally:
                session.close()
        """
        SessionLocal = get_session_factory(db_url)
        return SessionLocal()
    
    @staticmethod
    @contextmanager
    def session_scope(db_url: str):
        """Provide a transactional scope with automatic cleanup.
        
        Args:
            db_url: SQLAlchemy database URL
            
        Yields:
            SQLAlchemy Session instance
            
        Example:
            with DatabaseManager.session_scope(db_url) as session:
                vms = session.query(VirtualMachine).all()
                # Session is automatically closed
        """
        session = DatabaseManager.get_session(db_url)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @staticmethod
    def test_connection(db_url: str) -> tuple[bool, Optional[str]]:
        """Test database connection.
        
        Args:
            db_url: SQLAlchemy database URL
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            
        Example:
            success, error = DatabaseManager.test_connection(db_url)
            if success:
                st.success("Connected!")
            else:
                st.error(f"Connection failed: {error}")
        """
        try:
            engine = get_engine(db_url)
            with engine.connect() as conn:
                # Execute simple query to verify connection
                conn.execute(text("SELECT 1"))
            return True, None
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False, str(e)
    
    @staticmethod
    def clear_cache():
        """Clear all cached database resources.
        
        Use this when the database URL changes or to force reconnection.
        
        Example:
            if st.button("Reconnect"):
                DatabaseManager.clear_cache()
                st.rerun()
        """
        logger.info("Clearing database cache")
        # Clear Streamlit resource cache
        get_engine.clear()
        get_session_factory.clear()


def with_session(func):
    """Decorator for automatic session management.
    
    The decorated function should accept db_url as first argument
    and session as second argument.
    
    Example:
        @with_session
        def get_vm_count(db_url: str, session: Session) -> int:
            return session.query(func.count(VirtualMachine.id)).scalar()
        
        # Usage
        count = get_vm_count(db_url)
    """
    def wrapper(db_url: str, *args, **kwargs):
        with DatabaseManager.session_scope(db_url) as session:
            return func(db_url, session, *args, **kwargs)
    return wrapper
