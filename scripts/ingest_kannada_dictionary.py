#!/usr/bin/env python3
"""
VibeLyrics Kannada-English Dictionary Ingestion Pipeline
Parses data/KEED_2018-29-971.pdf, extracts Romanized Kannada vocabulary,
seeds the local SQLite database, generates a RAG/Search index, and compiles
an instruction fine-tuning dataset.
"""
import os
import sys
import re
import json
import sqlite3
import PyPDF2
from datetime import datetime

# Add root directory to sys.path so we can import services
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

from backend.services.rhyme_detector import RhymeDetector

PDF_PATH = os.path.join(ROOT_DIR, "data", "KEED_2018-29-971.pdf")
DB_PATH = os.path.join(ROOT_DIR, "data", "vibelyrics.db")
INDEX_PATH = os.path.join(ROOT_DIR, "data", "kannada_dictionary_index.json")
SFT_DIR = os.path.join(ROOT_DIR, "data", "training")
SFT_PATH = os.path.join(SFT_DIR, "kannada_dictionary_sft.json")

def parse_dictionary():
    print(f"[*] Opening PDF: {PDF_PATH}")
    if not os.path.exists(PDF_PATH):
        print(f"[!] PDF not found at {PDF_PATH}")
        return []

    print("[*] Extracting pages and parsing entries (this may take 1-2 minutes)...")
    
    parsed_entries = []
    
    # Boundary lookahead to identify starts of entries:
    # 1. Optional bullet symbol
    # 2. Kannada + garbled word: [^\x00-\x7F\s\-]+ (any non-ASCII word)
    # 3. Transliteration: ASCII letters + Latin Extended (\u00C0-\u024F) + Latin Extended Additional (\u1E00-\u1EFF)
    # 4. IPA block inside [...]
    entry_pattern = re.compile(
        r'(?:Ĺ|đ|♠|♢|\?|Ď)?'
        r'([^\x00-\x7F\s\-]+)'
        r'\s*([a-zA-Z\s\-\d¹²³⁴\'’‘\u00C0-\u024F\u1E00-\u1EFF]+?)'
        r'\s*\[([^\]]+)\]'
        r'\s*(.+?)(?=(?:Ĺ|đ|♠|♢|\?|Ď)?[^\x00-\x7F\s\-]+[a-zA-Z\s\-\d¹²³⁴\'’‘\u00C0-\u024F\u1E00-\u1EFF]+?\[[^\]]+\]|--- PAGE |$)'
    )

    with open(PDF_PATH, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)
        print(f"[*] Total PDF pages detected: {total_pages}")
        
        # We start scanning from page 3 to skip preface/intro, though lookahead handles it anyway
        for p in range(3, total_pages):
            if p % 100 == 0 or p == total_pages - 1:
                print(f"  -> Processing page {p}/{total_pages}...")
            
            try:
                page_text = reader.pages[p].extract_text()
                if not page_text:
                    continue
                
                # Normalize newlines and whitespace
                page_clean = " ".join(page_text.split())
                
                matches = entry_pattern.findall(page_clean)
                for match in matches:
                    kannada_raw = match[0].strip()
                    translit = match[1].strip()
                    ipa = match[2].strip()
                    rest = match[3].strip()
                    
                    # Optional POS and Category matching
                    pos_cat_match = re.match(
                        r'^([a-z\.,\s\+\-\?/\\_]+)?'
                        r'(?:ú([^û]+)û)?'
                        r'\s*(.+)$',
                        rest
                    )
                    
                    pos = ""
                    category = ""
                    definition = rest
                    
                    if pos_cat_match:
                        pos = pos_cat_match.group(1).strip() if pos_cat_match.group(1) else ""
                        category = pos_cat_match.group(2).strip() if pos_cat_match.group(2) else ""
                        definition = pos_cat_match.group(3).strip()
                    
                    # Clean up transliteration (remove superscript numbers, etc.)
                    translit_clean = re.sub(r'[¹²³⁴\d]', '', translit).strip().lower()
                    
                    # Skip empty transliterations or entries that are too short to be words
                    if not translit_clean or len(translit_clean) < 2:
                        continue
                        
                    parsed_entries.append({
                        "page": p,
                        "kannada_raw": kannada_raw,
                        "transliteration": translit_clean,
                        "ipa": ipa,
                        "pos": pos,
                        "category": category,
                        "definition": definition
                    })
            except Exception as e:
                print(f"[!] Error parsing page {p}: {e}")
                
    print(f"[OK] Extraction complete. Successfully parsed {len(parsed_entries)} dictionary entries.")
    return parsed_entries

def seed_sqlite_database(entries):
    print(f"[*] Opening SQLite database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"[!] Database not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='multisyllabic_words'")
    if not cursor.fetchone():
        print("[!] Table multisyllabic_words does not exist. Please run the app once to create the tables.")
        conn.close()
        return

    # Load existing words to prevent duplicate inserts
    cursor.execute("SELECT word FROM multisyllabic_words WHERE language = 'kn'")
    existing_words = {row[0].lower().strip() for row in cursor.fetchall()}
    print(f"[*] Found {len(existing_words)} existing Kannada words in database.")

    detector = RhymeDetector()
    words_to_insert = []
    
    print("[*] Performing phonetic analysis and preparing database records...")
    
    inserted_set = set()
    for entry in entries:
        word = entry["transliteration"]
        
        # Clean any trailing punctuation or special chars in the key
        word_clean = re.sub(r'[^a-zA-Zāīūśṣṭḍṅñṟēōṛḷ]', '', word).strip().lower()
        if not word_clean or len(word_clean) < 2 or word_clean in existing_words or word_clean in inserted_set:
            continue
            
        try:
            # Extract vowels, exact rhyme key, and syllable count using VibeLyrics RhymeDetector
            vowel_seq, exact_key, syllable_count = detector.extract_romanized_indian_vowels(word_clean, 'kn')
            
            if syllable_count > 0 and vowel_seq:
                inserted_set.add(word_clean)
                words_to_insert.append((
                    word_clean,
                    'kn',  # language
                    syllable_count,
                    vowel_seq,
                    exact_key,
                    0,     # is_slang (False)
                    5      # upvotes (standard level for seeded words)
                ))
        except Exception as e:
            print(f"[!] Phonetic extract error for {word_clean}: {e}")

    if words_to_insert:
        print(f"[*] Bulk inserting {len(words_to_insert)} unique Kannada words into multisyllabic_words...")
        try:
            cursor.executemany(
                """
                INSERT INTO multisyllabic_words (word, language, syllable_count, vowel_sequence, exact_rhyme_key, is_slang, upvotes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                words_to_insert
            )
            conn.commit()
            print(f"[OK] Database seeded successfully! {len(words_to_insert)} Kannada words added.")
        except Exception as e:
            conn.rollback()
            print(f"[!] Database bulk insert failed: {e}")
    else:
        print("[*] No new words to insert into database (all either already exist or are invalid).")

    conn.close()

def generate_rag_search_index(entries):
    print(f"[*] Generating local Search/RAG index at: {INDEX_PATH}")
    
    # Group duplicate transliterations to preserve alternative definitions
    index_dict = {}
    for entry in entries:
        word = entry["transliteration"]
        word_clean = re.sub(r'[^a-zA-Zāīūśṣṭḍṅñṟēōṛḷ]', '', word).strip().lower()
        if not word_clean:
            continue
            
        definition_text = entry["definition"]
        if entry["pos"]:
            definition_text = f"({entry['pos']}) {definition_text}"
        if entry["category"]:
            definition_text = f"[{entry['category']}] {definition_text}"
            
        if word_clean not in index_dict:
            index_dict[word_clean] = {
                "word": word_clean,
                "definitions": [definition_text],
                "ipa": entry["ipa"]
            }
        else:
            if definition_text not in index_dict[word_clean]["definitions"]:
                index_dict[word_clean]["definitions"].append(definition_text)
                
    # Save as JSON index
    with open(INDEX_PATH, 'w', encoding='utf-8') as out:
        json.dump(index_dict, out, indent=2, ensure_ascii=False)
        
    print(f"[OK] Saved {len(index_dict)} unique indexed definitions to {INDEX_PATH}")

def generate_sft_dataset(entries):
    print(f"[*] Generating local LLM SFT training dataset...")
    os.makedirs(SFT_DIR, exist_ok=True)
    
    sft_pairs = []
    seen = set()
    
    for entry in entries:
        word = entry["transliteration"]
        word_clean = re.sub(r'[^a-zA-Zāīūśṣṭḍṅñṟēōṛḷ]', '', word).strip().lower()
        if not word_clean or word_clean in seen:
            continue
            
        seen.add(word_clean)
        
        pos_str = f" ({entry['pos']})" if entry['pos'] else ""
        cat_str = f" [Category: {entry['category']}]" if entry['category'] else ""
        
        instruction = f"Define and translate the Romanized Kannada word to English."
        input_text = f"Word: {word_clean}"
        output_text = f"The Romanized Kannada word '{word_clean}' means: {entry['definition']}{pos_str}{cat_str}."
        
        sft_pairs.append({
            "instruction": instruction,
            "input": input_text,
            "output": output_text
        })
        
    with open(SFT_PATH, 'w', encoding='utf-8') as out:
        json.dump(sft_pairs, out, indent=2, ensure_ascii=False)
        
    print(f"[OK] Compiled {len(sft_pairs)} SFT training samples and saved to {SFT_PATH}")

def main():
    start_time = datetime.now()
    
    # 1. Parse dictionary PDF
    entries = parse_dictionary()
    if not entries:
        print("[!] No entries extracted. Exiting.")
        return
        
    # 2. Seed SQLite database
    seed_sqlite_database(entries)
    
    # 3. Generate Search/RAG index
    generate_rag_search_index(entries)
    
    # 4. Generate SFT LLM dataset
    generate_sft_dataset(entries)
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n[SUCCESS] Ingestion completed in {duration.total_seconds():.1f} seconds.")

if __name__ == "__main__":
    main()
