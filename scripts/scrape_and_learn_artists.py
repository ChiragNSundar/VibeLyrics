#!/usr/bin/env python3
"""
Bulk Scrape and Learn Script for VibeLyrics
Scrapes lyrics for Drake, PARTYNEXTDOOR, The Weeknd, Chris Brown, Tyga, and Tory Lanez
and extracts style/vocabulary patterns for the AI brain.
"""
import asyncio
import sys
import os
import random
import time
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

from backend.services.scraper import LyricsScraper
from backend.services.learning import StyleExtractor, VocabularyManager

# Set politeness delay to avoid IP blocks from AZLyrics
POLITENESS_DELAY_MIN = 2.5
POLITENESS_DELAY_MAX = 4.5

async def main():
    scraper = LyricsScraper()
    style_extractor = StyleExtractor()
    vocab_manager = VocabularyManager()
    
    artists = [
        "Drake",
        "PARTYNEXTDOOR",
        "The Weeknd",
        "Chris Brown",
        "Tyga",
        "Tory Lanez",
        "Kanye West"
    ]
    max_songs = 8
    
    all_lines = []
    all_words = []
    
    print(f"[*] Starting bulk scrape and learn process for: {', '.join(artists)}")
    print(f"[*] Target: {max_songs} songs per artist")
    
    for artist in artists:
        print(f"\n==================================================")
        print(f"[*] Processing Artist: {artist}")
        print(f"==================================================")
        
        try:
            async for event in scraper.scrape_artist_songs_stream(artist, max_songs=max_songs):
                if event["type"] == "progress":
                    print(f"  [Progress] {event['msg']}")
                elif event["type"] == "success":
                    print(f"  [Success] {event['msg']}")
                elif event["type"] == "warning":
                    print(f"  [Warning] {event['msg']}")
                elif event["type"] == "error":
                    print(f"  [Error] {event['msg']}")
                elif event["type"] == "done":
                    results = event.get("results", [])
                    print(f"  [+] Finished scraping {artist}. Successfully retrieved {len(results)} songs.")
                    for song in results:
                        text = song.get("lyrics", "")
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        all_lines.extend(lines)
                        for line in lines:
                            all_words.extend(line.lower().split())
        except Exception as e:
            print(f"  [!] Error processing {artist}: {e}")
            
    if all_lines:
        print(f"\n==================================================")
        print(f"[*] Bulk Processing & Learning Phase")
        print(f"==================================================")
        print(f"[*] Total lines parsed: {len(all_lines)}")
        print(f"[*] Total words tracked: {len(all_words)}")
        
        print("[*] Updating local Style Profile (user_style.json)...")
        style_extractor.learn_from_session(all_lines)
        print("[OK] Style Profile saved.")
        
        print("[*] Tracking vocabulary usage frequencies (vocabulary.json)...")
        vocab_manager.track_usage(all_words)
        print("[OK] Vocabulary usage frequencies updated.")
        
        print("[*] Mapping word co-occurrences for brain map (co_occurrences.json)...")
        vocab_manager.track_co_occurrences(all_lines)
        print("[OK] Neural connection map built.")
        
        print("\n[SUCCESS] Bulk learning process completed successfully!")
    else:
        print("\n[!] No lyrics were scraped successfully. Learning phase skipped.")

if __name__ == "__main__":
    asyncio.run(main())
