from pathlib import Path
import yaml


def test_openapi_parses():
    data = yaml.safe_load(Path("spec/mam-api.openapi.yaml").read_text())
    assert data["openapi"] == "3.1.0"
    assert data["components"]["securitySchemes"]["mamSession"]["in"] == "cookie"
    assert "/tor/js/loadSearchJSONbasic.php" in data["paths"]
