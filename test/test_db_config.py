"""Tests for database configuration."""
import unittest
import os
from unittest.mock import patch


class TestDatabaseConfig(unittest.TestCase):
    """Test database configuration paths."""
    
    def test_postgres_config(self):
        """Test PostgreSQL configuration is loaded correctly."""
        with patch.dict(os.environ, {
            "DB_BACKEND": "postgres",
            "POSTGRES_USER": "testuser",
            "POSTGRES_PASSWORD": "testpass",
            "POSTGRES_HOST": "testhost",
            "POSTGRES_PORT": "5433",
            "POSTGRES_DB": "testdb"
        }):
            # Need to reload the module to pick up env changes
            import importlib
            import db
            importlib.reload(db)
            
            # Verify the DATABASE_URL was constructed correctly
            expected_url = "postgresql://testuser:testpass@testhost:5433/testdb"
            self.assertEqual(db.DATABASE_URL, expected_url)
            
            # Reload back to sqlite for other tests
            with patch.dict(os.environ, {"DB_BACKEND": "sqlite"}):
                importlib.reload(db)


if __name__ == "__main__":
    unittest.main()
