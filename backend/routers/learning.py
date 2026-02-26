from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import asyncio

from ..services.scraper import LyricsScraper
from ..services.learning import StyleExtractor, VocabularyManager

router = APIRouter()
_scraper = LyricsScraper()
_style_extractor = StyleExtractor()
_vocab_manager = VocabularyManager()

class ScrapeRequest(BaseModel):
    artist: str
    max_songs: int = 3
    era: Optional[str] = None

@router.get("/learning/status")
async def get_learning_status() -> Dict[str, Any]:
    """Get the current learning dashboard metrics."""
    vocab_context = _vocab_manager.get_vocabulary_context()
    style_summary = _style_extractor.get_style_summary()
    
    return {
        "success": True,
        "vocabulary": {
            "favorites": vocab_context.get("favorites", []),
            "slangs": vocab_context.get("slangs", []),
            "most_used": vocab_context.get("most_used", [])[:15],
            "avoided": vocab_context.get("avoided", [])
        },
        "style": {
            "themes": style_summary.get("preferred_themes", []),
            "rhyme_preference": style_summary.get("rhyme_preference", "Not enough data"),
            "avg_line_length": style_summary.get("avg_line_length", 0)
        }
    }

async def _sse_learning_stream(artist: str, max_songs: int, era: str):
    """Generator for Server-Sent Events. Scrapes and learns simultaneously."""
    try:
        yield f"data: {json.dumps({'msg': f'Initializing scraping module for {artist}...'})}\n\n"
        
        all_lines = []
        all_words = []
        
        # Stream from scraper
        async for event in _scraper.scrape_artist_songs_stream(artist, max_songs, era):
            if event["type"] in ["progress", "success", "warning", "error"]:
                yield f"data: {json.dumps({'msg': event['msg']})}\n\n"
            
            if event["type"] == "done":
                results = event.get("results", [])
                yield f"data: {json.dumps({'msg': f'Scraping complete. Found {len(results)} songs. Processing lyrics...'})}\n\n"
                
                for song in results:
                    text = song.get("lyrics", "")
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    all_lines.extend(lines)
                    for line in lines:
                        all_words.extend(line.lower().split())
        
        # Feed into brain
        if all_lines:
            yield f"data: {json.dumps({'msg': f'Analyzing style from {len(all_lines)} lines...'})}\n\n"
            _style_extractor.learn_from_session(all_lines)
            
        if all_words:
            yield f"data: {json.dumps({'msg': f'Tracking vocabulary usage from {len(all_words)} words...'})}\n\n"
            _vocab_manager.track_usage(all_words)
            
        yield f"data: {json.dumps({'msg': 'Brain updated successfully! Redirecting...', 'done': True})}\n\n"
            
    except asyncio.CancelledError:
        print("[Learning System] Client disconnected stream.")
        raise
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@router.get("/learning/scrape/stream")
async def stream_learning_scrape(artist: str, max_songs: int = 3, era: str = None):
    """Start scraping lyrics and stream progress back to a Terminal UI."""
    if not artist:
        raise HTTPException(status_code=400, detail="Artist name is required")
        
    return StreamingResponse(
        _sse_learning_stream(artist, max_songs, era),
        media_type="text/event-stream"
    )

@router.post("/learning/upload")
async def upload_learning_document(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    """Feed the AI brain via manual document upload (.txt, .pdf, .docx) or text paste."""
    content = ""
    
    if text:
        content = text
    elif file:
        filename = file.filename.lower()
        file_bytes = await file.read()
        
        try:
            if filename.endswith(".txt"):
                content = file_bytes.decode("utf-8")
            elif filename.endswith(".pdf"):
                import PyPDF2
                from io import BytesIO
                pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        content += page_text + "\n"
            elif filename.endswith(".docx"):
                import docx
                from io import BytesIO
                doc = docx.Document(BytesIO(file_bytes))
                content = "\n".join([p.text for p in doc.paragraphs])
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format. Please use .txt, .pdf, or .docx")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Must provide either a file or raw text.")

    if not content.strip():
        raise HTTPException(status_code=400, detail="Document appears to be empty.")

    # Process extracted content
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    words = []
    for line in lines:
        words.extend(line.lower().split())

    if lines:
        _style_extractor.learn_from_session(lines)
    if words:
        _vocab_manager.track_usage(words)

    return {
        "success": True,
        "message": f"Successfully learned from document ({len(lines)} lines parsed).",
        "lines_parsed": len(lines),
        "words_parsed": len(words)
    }

@router.post("/learning/reset")
async def reset_learning_brain():
    """Wipe all learned style and vocabulary data completely."""
    _style_extractor.reset()
    _vocab_manager.reset()
    return {"success": True, "message": "AI Brain has been completely reset to default state."}

@router.delete("/learning/vocabulary")
async def delete_vocabulary_word(word: str, list_type: str = "most_used"):
    """
    Remove a specific word from the learned vocabulary.
    list_type can be 'favorites', 'slangs', 'avoided', or 'most_used'
    """
    word = word.lower().strip()
    
    if list_type in ["favorites", "slangs"]:
        _vocab_manager.remove_favorite(word)
    elif list_type == "avoided":
        _vocab_manager.remove_avoided(word)
    elif list_type == "most_used":
        # Remove from frequency counter
        if word in _vocab_manager.word_frequency:
            del _vocab_manager.word_frequency[word]
            _vocab_manager._save_vocabulary()
            
    return {"success": True, "message": f"Removed '{word}' from {list_type}."}
