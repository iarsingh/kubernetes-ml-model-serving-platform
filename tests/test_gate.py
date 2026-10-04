from fastapi.testclient import TestClient
from k8sml.main import app

client = TestClient(app)


def test_pass_and_fail():
    good = client.post("/check", json={'probes': True, 'hpa': True, 'image': 'serve:1.0.0'}).json()
    assert good["passed"] is True
    assert good["applied"] is False
    bad = client.post("/check", json={'probes': True, 'hpa': True, 'image': 'serve:latest'}).json()
    assert bad["passed"] is False
    assert "image_tag_latest" in bad["failed"]
