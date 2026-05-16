#!/usr/bin/env python
# scripts/cli_import_questions.py
"""
CLI tool for importing quiz questions
Usage: 
    python cli_import_questions.py --file <path> --lang <en|am|or>
    python cli_import_questions.py --folder <path> --lang <en|am|or>
    python cli_import_questions.py --status
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from admin_center_api.services.questions_import_service import QuestionsImportService


def parse_question_flag(argv):
    """Extract a --question_<book>.json flag from raw argv and return cleaned argv list.
    Example: --question_job.json -> questions_Job.json
    """
    question_file = None
    cleaned = []

    for a in argv:
        if a.startswith('--question_'):
            raw = a[len('--question_'):]
            if raw.endswith('.json'):
                raw = raw[:-5]
            # normalize to questions_Book.json
            if raw.lower().startswith('questions_'):
                stem = raw
            else:
                stem = f'questions_{raw}'
            # capitalize simple book name portion
            parts = stem.split('_', 1)
            if len(parts) == 2:
                question_file = f"{parts[0]}_{parts[1].capitalize()}.json"
            else:
                question_file = f"{stem}.json"
        else:
            cleaned.append(a)

    return question_file, cleaned

def main():
    # Pre-parse argv to support --question_<book>.json style flags
    question_flag, cleaned_argv = parse_question_flag(sys.argv[1:])

    parser = argparse.ArgumentParser(description='Import quiz questions into database')
    parser.add_argument('--file', type=str, help='Path to questions JSON file')
    parser.add_argument('--folder', type=str, help='Path to folder containing JSON files')
    # backward-compatible language arg
    parser.add_argument('--lang', type=str, choices=['en', 'am', 'or'], help='Language code (en, am, or)')
    # short language flags
    lang_group = parser.add_mutually_exclusive_group()
    lang_group.add_argument('--en', action='store_true', help='Import English questions')
    lang_group.add_argument('--am', action='store_true', help='Import Amharic questions')
    lang_group.add_argument('--or', dest='oromo', action='store_true', help='Import Oromo questions')
    parser.add_argument('--status', action='store_true', help='Show questions status')

    args = parser.parse_args(cleaned_argv)

    service = QuestionsImportService()

    if args.status:
        status = service.get_questions_status()
        print("\n📊 QUESTIONS IMPORT STATUS")
        print("="*40)
        print(f"Total questions: {status['total_questions']}")
        print(f"Questions by language: {status['questions_by_language']}")
        return

    # decide language
    language = None
    if args.lang:
        language = args.lang
    elif args.en:
        language = 'en'
    elif args.am:
        language = 'am'
    elif getattr(args, 'oromo', False):
        language = 'or'

    # if file not provided, but question flag present, use it
    file_arg = args.file
    if not file_arg and question_flag:
        file_arg = question_flag

    if file_arg and language:
        # Resolve file path: if plain filename, try default questions folder
        file_path = Path(file_arg)
        if not file_path.is_absolute() or not file_path.exists():
            # try project default location
            root = Path(__file__).parent.parent
            lang_map = {'en': 'english_bible', 'am': 'amharic_bible', 'or': 'oromifa_bible'}
            folder = root / 'app' / 'each_book_qestion_json_file' / 'Old_Testament' / lang_map.get(language, 'english_bible')
            candidate = folder / file_arg
            if candidate.exists():
                file_path = candidate

        print(f"📝 Importing questions from {file_path} ({language})...")
        result = service.import_questions_json(str(file_path), language)

        if result['success']:
            print(f"✅ {result['message']}")
            print(f"   Questions imported: {result['questions_imported']}")
        else:
            print(f"❌ Error: {result['message']}")
        return

    if args.folder and language:
        print(f"📚 Importing all questions from {args.folder} ({language})...")
        result = service.import_folder(args.folder, language)

        print(f"\n✅ Import complete!")
        print(f"   Total files: {result['total_files']}")
        print(f"   Successfully imported: {len(result['imported'])}")
        print(f"   Failed: {len(result['failed'])}")

        for item in result['imported']:
            print(f"   ✓ {item['book_name']}: {item['questions_imported']} questions")

        for item in result['failed']:
            print(f"   ✗ {item['file']}: {item['error']}")
        return

    parser.print_help()

if __name__ == "__main__":
    main()