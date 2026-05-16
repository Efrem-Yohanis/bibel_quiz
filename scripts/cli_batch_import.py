#!/usr/bin/env python
# scripts/cli_batch_import.py
"""
Batch import tool - Import both Bible texts and questions
Usage: python cli_batch_import.py --bible-folder <path> --questions-folder <path> --lang <en|am|or>
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from admin_center_api.services.bible_import_service import BibleImportService
from admin_center_api.services.questions_import_service import QuestionsImportService

def main():
    parser = argparse.ArgumentParser(description='Batch import Bible texts and questions')
    parser.add_argument('--bible-folder', type=str, help='Path to folder containing Bible text files')
    parser.add_argument('--questions-folder', type=str, help='Path to folder containing questions JSON files')
    parser.add_argument('--lang', type=str, required=True, choices=['en', 'am', 'or'], help='Language code')
    parser.add_argument('--bible-only', action='store_true', help='Import only Bible texts')
    parser.add_argument('--questions-only', action='store_true', help='Import only questions')
    
    args = parser.parse_args()
    
    if args.bible_only:
        # Import only Bible
        if not args.bible_folder:
            print("❌ Please provide --bible-folder")
            return
        
        print("📖 Importing Bible texts...")
        bible_service = BibleImportService()
        result = bible_service.import_folder(args.bible_folder, args.lang)
        
        print(f"\n✅ Bible import complete!")
        print(f"   Imported: {len(result['imported'])} files")
        print(f"   Failed: {len(result['failed'])} files")
        
    elif args.questions_only:
        # Import only questions
        if not args.questions_folder:
            print("❌ Please provide --questions-folder")
            return
        
        print("📝 Importing questions...")
        questions_service = QuestionsImportService()
        result = questions_service.import_folder(args.questions_folder, args.lang)
        
        print(f"\n✅ Questions import complete!")
        print(f"   Imported: {len(result['imported'])} files")
        print(f"   Failed: {len(result['failed'])} files")
        
    else:
        # Import both
        if not args.bible_folder or not args.questions_folder:
            print("❌ Please provide both --bible-folder and --questions-folder")
            return
        
        print("="*50)
        print("📖 BATCH IMPORT STARTED")
        print("="*50)
        
        # Import Bible
        print("\n1. Importing Bible texts...")
        bible_service = BibleImportService()
        bible_result = bible_service.import_folder(args.bible_folder, args.lang)
        
        print(f"   ✓ Imported: {len(bible_result['imported'])} books")
        
        # Import Questions
        print("\n2. Importing questions...")
        questions_service = QuestionsImportService()
        questions_result = questions_service.import_folder(args.questions_folder, args.lang)
        
        print(f"   ✓ Imported: {len(questions_result['imported'])} question files")
        
        print("\n" + "="*50)
        print("✅ BATCH IMPORT COMPLETE")
        print("="*50)
        print(f"Bible books imported: {len(bible_result['imported'])}")
        print(f"Question files imported: {len(questions_result['imported'])}")

if __name__ == "__main__":
    main()