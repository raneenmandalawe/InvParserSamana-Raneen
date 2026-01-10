# test/conftest.py
import sys
import importlib
import pytest
from unittest.mock import patch


@pytest.fixture()
def app_module():
    """
    Import app.py with OCI patched so that:
    - oci.config.from_file() won't try to read ~/.oci/config
    - AIServiceDocumentClient won't hit the network
    """
    with patch("oci.config.from_file", return_value={}), patch(
        "oci.ai_document.AIServiceDocumentClient"
    ) as mock_client_cls:
        # Ensure a fresh import each test to keep isolation clean
        if "app" in sys.modules:
            del sys.modules["app"]

        import app  # noqa: F401
        importlib.reload(app)

        # Expose the mocked class to tests (optional convenience)
        app._mock_client_cls = mock_client_cls
        return app
