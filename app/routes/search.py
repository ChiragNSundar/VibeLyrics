"""
Search Routes
Full-text search API endpoints
"""
from flask import Blueprint, request, jsonify

search_bp = Blueprint('search', __name__)


@search_bp.route('/search', methods=['GET'])
def search_lyrics():
    """
    Full-text search across all lyrics.
    
    Query params:
        q: Search query (required)
        limit: Max results (default 20)
        session_id: Filter by session (optional)
        fuzzy: Enable fuzzy matching (default true)
    """
    from app.search import get_search_index
    
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)
    session_id = request.args.get('session_id', type=int)
    fuzzy = request.args.get('fuzzy', 'true').lower() == 'true'
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    search_index = get_search_index()
    results = search_index.search(
        query=query,
        limit=limit,
        session_id=session_id,
        fuzzy=fuzzy
    )
    
    return jsonify({
        "success": True,
        "query": query,
        "count": len(results),
        "results": results
    })


@search_bp.route('/search/rhymes', methods=['GET'])
def search_rhymes():
    """
    Find lines that rhyme with a given word.
    
    Query params:
        word: Word to find rhymes for (required)
        limit: Max results (default 30)
    """
    from app.search import get_search_index
    
    word = request.args.get('word', '').strip()
    limit = request.args.get('limit', 30, type=int)
    
    if not word:
        return jsonify({"error": "Query parameter 'word' is required"}), 400
    
    search_index = get_search_index()
    results = search_index.search_rhymes(word=word, limit=limit)
    
    return jsonify({
        "success": True,
        "word": word,
        "count": len(results),
        "rhymes": results
    })


@search_bp.route('/search/reindex', methods=['POST'])
def reindex():
    """Rebuild the entire search index from database"""
    from app.search import get_search_index
    
    search_index = get_search_index()
    stats = search_index.reindex_all()
    
    return jsonify({
        "success": True,
        "message": "Reindexing complete",
        **stats
    })


@search_bp.route('/search/stats', methods=['GET'])
def search_stats():
    """Get search index statistics"""
    from app.search import get_search_index
    
    search_index = get_search_index()
    stats = search_index.get_stats()
    
    return jsonify({
        "success": True,
        **stats
    })
