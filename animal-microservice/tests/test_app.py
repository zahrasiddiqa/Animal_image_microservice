import pytest
from pathlib import Path
from app import create_app
import requests

class FakeResponse:
    def __init__(self, content=b'fakeimagebytes', status_code=200):
        self.status_code = status_code
        self._content = content
    def iter_content(self, chunk_size=8192):
        yield self._content

def fake_get(url, stream=True, timeout=10):
    return FakeResponse()

def test_fetch_and_last(tmp_path, monkeypatch):
    db = tmp_path / 'test.db'
    images = tmp_path / 'images'
    images.mkdir()
    app = create_app({'DATABASE': str(db), 'IMAGES_DIR': str(images), 'TESTING': True})
    monkeypatch.setattr(requests, 'get', fake_get)
    client = app.test_client()

    r = client.post('/api/fetch?animal=cat&count=2')
    assert r.status_code == 200
    j = r.get_json()
    assert 'saved' in j and len(j['saved']) == 2

    for s in j['saved']:
        f = images / s['filename']
        assert f.exists()

    r2 = client.get('/api/last?animal=cat')
    assert r2.status_code == 200
    last = r2.get_json()
    assert last['animal'] == 'cat'
    assert 'image_url' in last
