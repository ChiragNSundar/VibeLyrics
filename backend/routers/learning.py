from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import asyncio

from ..services.scraper import LyricsScraper
from ..services.learning import StyleExtractor, VocabularyManager
from ..services.advanced_analysis import ComplexityScorer, PunchlineEngine, ImageryAnalyzer

router = APIRouter()
_scraper = LyricsScraper()
_style_extractor = StyleExtractor()
_vocab_manager = VocabularyManager()
_complexity_scorer = ComplexityScorer()
_punchline_engine = PunchlineEngine()
_imagery_analyzer = ImageryAnalyzer()

# In-memory store for last scraped lyrics (for annotations)
_last_scraped_lines: list = []

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

        # Track co-occurrences for brain map
        if all_lines:
            yield f"data: {json.dumps({'msg': 'Building neural connections for Brain Map...'})}\n\n"
            _vocab_manager.track_co_occurrences(all_lines)

        # Store for annotations
        global _last_scraped_lines
        _last_scraped_lines = all_lines[:200]  # Keep last 200 lines
            
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


@router.get("/learning/brain-map")
async def get_brain_map():
    """Get nodes and links for the interactive brain map force graph."""
    data = _vocab_manager.get_brain_map_data()
    return {"success": True, **data}


@router.get("/learning/dna")
async def get_lyrical_dna():
    """
    Compute lyrical DNA scores across 6 axes for a radar chart.
    Runs analysis over the user's learned data.
    """
    # Get all learned lines from style data
    style = _style_extractor.style_data
    avg_len = style.get("structure", {}).get("avg_line_length", 8)
    themes = style.get("themes", {}).get("preferred", [])
    vocab = _vocab_manager.get_vocabulary_context()
    freq = _vocab_manager.word_frequency

    # Vocabulary Richness: unique words / total words
    total_tracked = sum(freq.values()) if freq else 1
    unique_tracked = len(freq) if freq else 0
    vocab_richness = min(100, int((unique_tracked / max(1, total_tracked)) * 500))

    # Rhyme preference complexity
    rhyme_pref = style.get("rhyme", {}).get("scheme_preference", "AABB")
    rhyme_score = {"ABAB": 80, "AABB": 60, "XAXA": 70, "free": 40}.get(rhyme_pref, 50)

    # Punchline power — score a sample of top lines
    sample_lines = _last_scraped_lines[:20] if _last_scraped_lines else []
    if sample_lines:
        punch_scores = [_punchline_engine.score_punchline(l)["score"] for l in sample_lines]
        punchline_power = int(sum(punch_scores) / len(punch_scores))
    else:
        punchline_power = 0

    # Imagery density
    if sample_lines:
        imagery = _imagery_analyzer.analyze_imagery(sample_lines)
        imagery_density = min(100, int(imagery["density"] * 1000))
    else:
        imagery_density = 0

    # Line length variety
    line_variety = min(100, int(avg_len * 8))

    # Internal rhyme % (estimated from rhyme config)
    internal_freq = style.get("rhyme", {}).get("internal_rhyme_frequency", "low")
    internal_score = {"high": 85, "moderate": 55, "low": 25}.get(internal_freq, 30)

    return {
        "success": True,
        "axes": [
            {"axis": "Vocabulary Richness", "value": vocab_richness},
            {"axis": "Rhyme Complexity", "value": rhyme_score},
            {"axis": "Punchline Power", "value": punchline_power},
            {"axis": "Imagery Density", "value": imagery_density},
            {"axis": "Line Length Variety", "value": line_variety},
            {"axis": "Internal Rhyme %", "value": internal_score},
        ]
    }


@router.get("/learning/annotations")
async def get_annotations():
    """Auto-generate annotations for the last scraped lyrics using local engines."""
    if not _last_scraped_lines:
        return {"success": True, "annotations": [], "message": "No scraped lyrics available. Scrape an artist first."}

    annotations = []
    for line in _last_scraped_lines[:30]:  # Annotate up to 30 lines
        punch = _punchline_engine.score_punchline(line)
        techniques = punch.get("techniques", [])

        notes = []
        if "contrast" in techniques:
            notes.append("Contains contrast — possible double meaning")
        if "wordplay" in techniques:
            notes.append("Wordplay detected")
        if "double_entendre" in techniques:
            notes.append("Potential double entendre")
        if "internal_rhyme" in techniques:
            notes.append(f"Internal rhyme ({punch['internal_rhymes']} pairs)")
        if "alliteration" in techniques:
            notes.append(f"Alliterative ({punch['alliteration']} pairs)")

        # Check for simile/metaphor
        lower = line.lower()
        if " like " in lower or " as " in lower:
            notes.append("Simile detected")
        if any(w in lower for w in ["is a", "was a", "are the", "become"]):
            notes.append("Possible metaphor")

        annotations.append({
            "line": line,
            "score": punch["score"],
            "techniques": techniques,
            "notes": notes
        })

    return {"success": True, "annotations": annotations}


@router.post("/learning/audio")
async def upload_audio_for_analysis(
    file: UploadFile = File(...)
):
    """Upload an audio file (.mp3/.wav) to extract BPM, key, and energy via librosa."""
    filename = file.filename.lower()
    if not filename.endswith((".mp3", ".wav")):
        raise HTTPException(status_code=400, detail="Only .mp3 and .wav files are supported.")

    file_bytes = await file.read()

    try:
        import librosa
        from io import BytesIO
        import soundfile as sf
        import numpy as np

        # Load audio
        audio_data, sr = sf.read(BytesIO(file_bytes))
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)  # Convert to mono
        audio_data = audio_data.astype(np.float32)

        # Extract BPM
        tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sr)
        bpm = float(tempo) if not hasattr(tempo, '__len__') else float(tempo[0])

        # Extract energy (RMS)
        rms = librosa.feature.rms(y=audio_data)[0]
        avg_energy = float(np.mean(rms))
        energy_label = "High" if avg_energy > 0.1 else "Medium" if avg_energy > 0.04 else "Low"

        # Extract chroma for key estimation
        chroma = librosa.feature.chroma_cqt(y=audio_data, sr=sr)
        key_index = int(np.argmax(np.mean(chroma, axis=1)))
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        estimated_key = keys[key_index]

        # Save to style extractor
        _style_extractor.style_data.setdefault("audio", {})
        _style_extractor.style_data["audio"]["last_bpm"] = round(bpm)
        _style_extractor.style_data["audio"]["last_key"] = estimated_key
        _style_extractor.style_data["audio"]["last_energy"] = energy_label

        # Track BPM history
        bpm_history = _style_extractor.style_data["audio"].setdefault("bpm_history", [])
        bpm_history.append(round(bpm))
        if len(bpm_history) > 20:
            bpm_history[:] = bpm_history[-20:]

        _style_extractor.save_style()

        return {
            "success": True,
            "bpm": round(bpm),
            "key": estimated_key,
            "energy": energy_label,
            "avg_rms": round(avg_energy, 4)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio analysis failed: {str(e)}")
