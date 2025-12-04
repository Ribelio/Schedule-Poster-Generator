import pytest
from unittest.mock import MagicMock, patch
from manga_fetcher import MangaDexFetcher

@pytest.fixture
def fetcher():
    return MangaDexFetcher()

def test_get_manga_id_success(fetcher):
    # Mock response for searching manga
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": "ok",
        "data": [
            {
                "id": "test-manga-id",
                "attributes": {
                    "title": {"en": "Test Manga"}
                }
            }
        ]
    }
    mock_response.status_code = 200

    with patch('requests.get', return_value=mock_response) as mock_get:
        manga_id = fetcher.get_manga_id("Test Manga")
        assert manga_id == "test-manga-id"
        mock_get.assert_called_once()

def test_get_manga_id_not_found(fetcher):
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": "ok", "data": []}
    mock_response.status_code = 200

    with patch('requests.get', return_value=mock_response):
        manga_id = fetcher.get_manga_id("Nonexistent Manga")
        assert manga_id is None

def test_get_volume_covers(fetcher):
    # Mock response for covers
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": "ok",
        "data": [
            {
                "attributes": {
                    "volume": "1",
                    "fileName": "vol1.jpg"
                }
            },
            {
                "attributes": {
                    "volume": "2",
                    "fileName": "vol2.jpg"
                }
            }
        ]
    }
    
    with patch('requests.get', return_value=mock_response):
        covers = fetcher.get_volume_covers("manga-id", {1, 2})
        
        assert len(covers) == 2
        assert covers[1] == "https://uploads.mangadex.org/covers/manga-id/vol1.jpg"
        assert covers[2] == "https://uploads.mangadex.org/covers/manga-id/vol2.jpg"

def test_get_volume_covers_partial(fetcher):
    # Test when some volumes are missing
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": "ok",
        "data": [
            {
                "attributes": {
                    "volume": "1",
                    "fileName": "vol1.jpg"
                }
            }
        ]
    }
    
    with patch('requests.get', return_value=mock_response):
        covers = fetcher.get_volume_covers("manga-id", {1, 99})
        
        assert len(covers) == 1
        assert 1 in covers
        assert 99 not in covers
