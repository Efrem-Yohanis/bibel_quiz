#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from admin_center_api.services.questions_import_service import QuestionsImportService

LANGUAGE_FOLDERS = {
    'en': 'english_bible',
    'am': 'amharic_bible',
    'or': 'oromifa_bible'
}

DEFAULT_BOOK_PATH = ROOT / 'app' / 'each_book_qestion_json_file' / 'Old_Testament'


def parse_question_flag(argv):
    question_file = None
    cleaned = []

    for arg in argv:
        if arg.startswith('--question_'):
            raw_name = arg[len('--question_'):]
            if raw_name.endswith('.json'):
                raw_name = raw_name[:-5]
            if raw_name.startswith('questions_'):
                question_file = f"{raw_name}.json"
            elif raw_name.startswith('question_'):
                book_name = raw_name[len('question_'):]
                question_file = f"questions_{book_name.capitalize()}.json"
            else:
                question_file = f"questions_{raw_name.capitalize()}.json"
        else:
            cleaned.append(arg)

    return question_file, cleaned


def build_default_file_path(language_code: str, book_name: str) -> Path:
    folder = DEFAULT_BOOK_PATH / LANGUAGE_FOLDERS[language_code]
    stem = book_name
    if stem.lower().startswith('questions_'):
        stem = stem[len('questions_'):]
    if stem.lower().endswith('.json'):
        stem = stem[:-5]
    filename = f"questions_{stem.capitalize()}.json"
    return folder / filename


def determine_language(args):
    if args.en:
        return 'en'
    if args.am:
        return 'am'
    if args.oromo:
        return 'or'
    return None


def main():
    question_file_flag, cleaned_args = parse_question_flag(sys.argv[1:])

    parser = argparse.ArgumentParser(
        description='Import quiz questions into the Bible quiz database'
    )

    lang_group = parser.add_mutually_exclusive_group(required=True)
    lang_group.add_argument('--en', action='store_true', help='Import English questions')
    lang_group.add_argument('--am', action='store_true', help='Import Amharic questions')
    lang_group.add_argument('--or', dest='oromo', action='store_true', help='Import Oromo questions')

    parser.add_argument('--file', type=str, help='Path to a questions JSON file')
    parser.add_argument('--book', type=str, help='Book name or question file stem, e.g. Job or questions_Job.json')
    parser.add_argument('--status', action='store_true', help='Show import status')

    args = parser.parse_args(cleaned_args)

    service = QuestionsImportService()

    if args.status:
        status = service.get_questions_status()
        print('\n📊 QUESTIONS IMPORT STATUS')
        print('=' * 40)
        print(f"Total questions: {status['total_questions']}")
        print(f"Questions by language: {status['questions_by_language']}")
        return

    language_code = determine_language(args)
    if not language_code:
        parser.error('Please specify one language flag: --en, --am, or --or')

    file_path = None
    if args.file:
        file_path = Path(args.file)
    elif question_file_flag:
        file_path = Path(question_file_flag)
    elif args.book:
        file_path = build_default_file_path(language_code, args.book)
    else:
        parser.error('Please specify a question file using --file, --book, or a --question_<book>.json flag.')

    if not file_path.is_absolute():
        file_path = ROOT / file_path

    if not file_path.exists():
        print(f'❌ File not found: {file_path}')
        return

    print(f"📝 Importing questions from {file_path} ({language_code})...")
    result = service.import_questions_json(str(file_path), language_code)

    if result.get('success'):
        print(f"✅ {result['message']}")
        print(f"   Questions imported: {result.get('questions_imported', 0)}")
        print(f"   Book: {result.get('book_name')}")
        print(f"   Language: {result.get('language')}")
    else:
        print(f"❌ Error: {result.get('message')}")


if __name__ == '__main__':
    main()
