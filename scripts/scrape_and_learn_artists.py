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
        
        # Override the random sleep in the scraper stream to make it more polite
        # by executing the scraping steps carefully
        era_term = ""
        query = f"\"{artist}\"{era_term} lyrics site:azlyrics.com"
        
        print(f"  -> Querying search engine: {query}")
        try:
            results = list(scraper.ddgs.text(query, max_results=max_songs + 10))
            if not results:
                print(f"  [!] No search results found for {artist}")
                continue
                
            print(f"  -> Found {len(results)} potential lyrics URLs. Extracting...")
            
            seen_urls = set()
            artist_slug = re.sub(r'[^a-z0-9]', '', artist.lower())
            artist_scraped = 0
            
            for result in results:
                if artist_scraped >= max_songs:
                    break
                    
                url = result.get('link') or result.get('href', '')
                if 'azlyrics.com/lyrics' in url and url not in seen_urls:
                    if f'/lyrics/{artist_slug}/' in url.lower():
                        seen_urls.add(url)
                    
                    import re
                    title_match = re.search(r'/([^/]+)\.html$', url)
                    title = title_match.group(1).replace('', ' ').title() if title_match else "Unknown Track"
                    title_clean = " ".join(title.split())
                    
                    print(f"  -> Scraping lyrics for: '{title_clean}' ({url})...")
                    lyrics = scraper._scrape_azlyrics(url)
                    
                    if lyrics:
                        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
                        all_lines.extend(lines)
                        for line in lines:
                            all_words.extend(line.lower().split())
                        
                        artist_scraped += 1
                        print(f"     [OK] Extracted successfully ({len(lines)} lines).")
                    else:
                        print(f"     [!] Failed to extract lyrics from {url}")
                        
                    # Extra politeness delay to protect IP reputation
                    delay = random.uniform(POLITENESS_DELAY_MIN, POLITENESS_DELAY_MAX)
                    print(f"     [Politeness Pause] Waiting {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                    
            print(f"  [+] Finished scraping {artist}. Successfully retrieved {artist_scraped} songs.")
            
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
