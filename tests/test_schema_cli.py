"""Tests for schema CLI commands."""

import pytest
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner
from sqlalchemy import create_engine

from src.cli import cli
from src.models import Base
from src.services.schema_service import CURRENT_SCHEMA_VERSION


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def test_db_url():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Create database with schema
    db_url = f"sqlite:///{path}"
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    engine.dispose()
    
    yield db_url
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


def test_schema_version_command(runner, test_db_url):
    """Test schema-version command."""
    result = runner.invoke(cli, ['schema-version', '--db-url', test_db_url])
    
    assert result.exit_code == 0
    assert 'Schema Version Information' in result.output
    assert CURRENT_SCHEMA_VERSION in result.output
    assert 'Expected version:' in result.output


def test_schema_version_with_history(runner, test_db_url):
    """Test schema-version command with --history flag."""
    result = runner.invoke(cli, ['schema-version', '--history', '--db-url', test_db_url])
    
    assert result.exit_code == 0
    assert 'Schema Version Information' in result.output
    assert 'Version History' in result.output or 'No version history' in result.output


def test_schema_info_command(runner, test_db_url):
    """Test schema-info command."""
    result = runner.invoke(cli, ['schema-info', '--db-url', test_db_url])
    
    assert result.exit_code == 0
    assert 'Database Schema Information' in result.output
    assert 'Version:' in result.output
    assert 'Tables' in result.output
    assert 'Metadata:' in result.output


def test_schema_upgrade_command(runner, test_db_url):
    """Test schema-upgrade command with force flag."""
    result = runner.invoke(cli, ['schema-upgrade', '--force', '--db-url', test_db_url])
    
    # Should succeed or indicate already at latest version
    assert result.exit_code == 0
    assert 'Database Schema Upgrade' in result.output or 'already at the latest version' in result.output


def test_schema_commands_with_nonexistent_db(runner):
    """Test schema commands handle errors gracefully."""
    invalid_db = 'sqlite:///nonexistent/path/test.db'
    
    # schema-version should handle gracefully
    result = runner.invoke(cli, ['schema-version', '--db-url', invalid_db])
    # It should not crash, but show uninitialized status
    assert 'uninitialized' in result.output.lower() or 'schema tracking needs initialization' in result.output.lower()
