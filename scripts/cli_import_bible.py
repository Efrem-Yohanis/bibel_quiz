#!/usr/bin/env python
# scripts/cli_import_bible.py
"""
CLI tool for importing Bible texts
Usage: 
    python cli_import_bible.py --file <path> --lang <en|am|or>
    python cli_import_bible.py --folder <path> --lang <en|am|or>
    python cli_import_bible.py --status
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from admin_center_api.services.bible_import_service import BibleImportService

def main():
    parser = argparse.ArgumentParser(description='Import Bible texts into database')
    parser.add_argument('--file', type=str, help='Path to Bible text file')
    parser.add_argument('--folder', type=str, help='Path to folder containing Bible text files')
    parser.add_argument('--lang', type=str, choices=['en', 'am', 'or'], help='Language code (en, am, or)')
    parser.add_argument('--status', action='store_true', help='Show import status')
    
    args = parser.parse_args()
    
    service = BibleImportService()
    
    if args.status:
        status = service.get_import_status()
        print("\n📊 BIBLE IMPORT STATUS")
        print("="*40)
        print(f"Books imported: {status['books_imported']}")
        print(f"Verses imported: {status['verses_imported']}")
        print(f"Verse texts by language: {status['verse_texts_by_language']}")
        print(f"Languages available: {status['languages_available']}")
        return
    
    if args.file and args.lang:
        print(f"📖 Importing {args.file} ({args.lang})...")
        result = service.import_book(args.file, args.lang)
        
        if result['success']:
            print(f"✅ {result['message']}")
            print(f"   Verses imported: {result['verses_imported']}")
        else:
            print(f"❌ Error: {result['message']}")
        return
    
    if args.folder and args.lang:
        print(f"📚 Importing all books from {args.folder} ({args.lang})...")
        result = service.import_folder(args.folder, args.lang)
        
        print(f"\n✅ Import complete!")
        print(f"   Total files: {result['total_files']}")
        print(f"   Successfully imported: {len(result['imported'])}")
        print(f"   Failed: {len(result['failed'])}")
        
        for item in result['imported']:
            print(f"   ✓ {item['book_name']}: {item['verses_imported']} verses")
        
        for item in result['failed']:
            print(f"   ✗ {item['file']}: {item['error']}")
        return
    
    parser.print_help()

if __name__ == "__main__":
    main()