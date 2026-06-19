import pytest
from httpx import AsyncClient
from backend.services.dictionary_search import DictionarySearchService, get_dictionary_search


def test_dictionary_service_unit():
    # Instantiate service
    service = DictionarySearchService()
    # Mock its dictionary data
    service.dictionary = {
        "ibbaru": {
            "word": "ibbaru",
            "definitions": ["(mf.) two persons"],
            "ipa": "ibbə̆ru"
        },
        "ibbani": {
            "word": "ibbani",
            "definitions": ["(n.) dew, fog, frost"],
            "ipa": "ibbəni"
        },
        "innu": {
            "word": "innu",
            "definitions": ["(adv.) yet, still, more"],
            "ipa": "innu"
        }
    }
    service.loaded = True

    # Test exact lookup
    assert service.lookup_word("ibbaru")["word"] == "ibbaru"
    assert service.lookup_word("IBBARU")["word"] == "ibbaru"
    assert service.lookup_word("ibbani!")["word"] == "ibbani"
    assert service.lookup_word("nonexistent") is None

    # Test search by word (prefix/substring)
    prefix_results = service.search("ibba")
    assert len(prefix_results) == 2
    words = [r["word"] for r in prefix_results]
    assert "ibbaru" in words
    assert "ibbani" in words

    # Test search by definition content
    def_results = service.search("dew")
    assert len(def_results) == 1
    assert def_results[0]["word"] == "ibbani"

    # Test extract context from text
    context_results = service.extract_context_from_text("Here are two persons: ibbaru, standing in the ibbani dew")
    assert len(context_results) == 2
    words_extracted = [r["word"] for r in context_results]
    assert "ibbaru" in words_extracted
    assert "ibbani" in words_extracted


@pytest.mark.asyncio
async def test_dictionary_search_api(client: AsyncClient, monkeypatch):
    # Mock the global dictionary search service to return mock results
    service = get_dictionary_search()
    monkeypatch.setattr(service, "dictionary", {
        "ibbaru": {
            "word": "ibbaru",
            "definitions": ["(mf.) two persons"],
            "ipa": "ibbə̆ru"
        }
    })
    monkeypatch.setattr(service, "loaded", True)

    response = await client.get("/api/vocabulary/dictionary/search?query=ibba")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["query"] == "ibba"
    assert len(data["results"]) == 1
    assert data["results"][0]["word"] == "ibbaru"
