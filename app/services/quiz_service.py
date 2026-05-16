# app/services/quiz_service.py
"""
Quiz Service - Manages quiz with one-by-one question flow
"""

import sqlite3
import json
import random
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import re

DB_PATH = Path(__file__).parent.parent / 'bible_quiz.db'

class QuizService:
    """Service for quiz operations with one-by-one question flow"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def get_db(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ==================== Helper Methods ====================
    
    def get_language_id(self, language_code: str) -> Optional[int]:
        """Get language ID from code"""
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM languages WHERE code = ?", (language_code,))
        result = cursor.fetchone()
        conn.close()
        return result['id'] if result else None
    
    def get_level_id(self, level_number: int) -> Optional[int]:
        """Get level ID from level number"""
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM levels WHERE level_number = ?", (level_number,))
        result = cursor.fetchone()
        conn.close()
        return result['id'] if result else None
    
    def get_book_name(self, book_id: int) -> str:
        """Get book name by ID"""
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM books WHERE id = ?", (book_id,))
        result = cursor.fetchone()
        conn.close()
        return result['name'] if result else 'Unknown'
    
    # ==================== API Methods ====================
    
    def get_books(self) -> List[Dict]:
        """Get all books that have questions with level breakdown"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get all books that have questions
        cursor.execute("""
            SELECT DISTINCT b.id, b.name
            FROM books b
            JOIN questions q ON q.book_id = b.id
            ORDER BY b.id
        """)
        
        books = cursor.fetchall()
        
        result = []
        for book in books:
            book_id = book['id']
            book_name = book['name']
            
            # Get question count by level for this book
            cursor.execute("""
                SELECT l.id as level_id, l.level_number, l.name as level_name, COUNT(q.id) as question_count
                FROM questions q
                JOIN levels l ON q.level_id = l.id
                WHERE q.book_id = ?
                GROUP BY l.id
                ORDER BY l.level_number
            """, (book_id,))
            
            levels = cursor.fetchall()
            
            total_questions = sum(level['question_count'] for level in levels)
            
            levels_list = []
            for level in levels:
                levels_list.append({
                    'level_id': level['level_id'],
                    'name': level['level_name'],
                    'question_count': level['question_count']
                })
            
            result.append({
                'book_id': book_id,
                'name': book_name,
                'total_questions': total_questions,
                'levels': levels_list
            })
        
        conn.close()
        return result
    
    def get_languages(self) -> List[Dict]:
        """Get all active languages"""
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id as language_id, code, name, native_name 
            FROM languages WHERE is_active = 1
        """)
        languages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return languages
    
    def get_book_levels(self, book_id: int) -> Dict:
        """Get available levels for a book"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT l.id as level_id, l.level_number, l.name
            FROM questions q
            JOIN levels l ON q.level_id = l.id
            WHERE q.book_id = ?
            ORDER BY l.level_number
        """, (book_id,))
        
        levels = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        book_name = self.get_book_name(book_id)
        
        return {
            'book_id': book_id,
            'book_name': book_name,
            'levels': levels
        }
    
    def get_quizzes_by_book_level(self, book_id: int, level_id: int) -> Dict:
        """Get quizzes (chapters) for a book and level"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT 
                c.chapter_number,
                COUNT(q.id) as total_questions
            FROM questions q
            JOIN chapters c ON q.chapter_id = c.id
            WHERE q.book_id = ? AND q.level_id = ?
            GROUP BY c.chapter_number
            ORDER BY c.chapter_number
        """, (book_id, level_id))
        
        chapters = cursor.fetchall()
        conn.close()
        
        book_name = self.get_book_name(book_id)
        
        quizzes = []
        for chapter in chapters:
            quizzes.append({
                'quiz_id': chapter['chapter_number'],
                'title': f"{book_name} Chapter {chapter['chapter_number']} Quiz",
                'total_questions': chapter['total_questions'],
                'chapter': chapter['chapter_number']
            })
        
        return {
            'book_id': book_id,
            'book_name': book_name,
            'level_id': level_id,
            'quizzes': quizzes
        }
    
    def start_quiz(self, user_id: int, book_id: int, level_id: int, language_id: int) -> Dict:
        """Start a new quiz session"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get all question IDs for this book and level
        cursor.execute("""
            SELECT q.id
            FROM questions q
            WHERE q.book_id = ? AND q.level_id = ?
            ORDER BY q.id
        """, (book_id, level_id))
        
        questions = cursor.fetchall()
        
        if not questions:
            conn.close()
            return {'error': 'No questions found for this book and level'}
        
        # Extract question IDs and shuffle them
        question_ids = [q['id'] for q in questions]
        random.shuffle(question_ids)
        
        total_questions = len(question_ids)
        
        # Create resume data
        resume_data = {
            'question_ids': question_ids,
            'current_index': 0,
            'answers': [],
            'book_id': book_id,
            'level_id': level_id,
            'language_id': language_id
        }
        
        # Create quiz attempt
        cursor.execute("""
            INSERT INTO quiz_attempts (user_id, book_id, level_id, language_id, 
                                       total_questions, status, started_at, resume_data)
            VALUES (?, ?, ?, ?, ?, 'in_progress', ?, ?)
        """, (user_id, book_id, level_id, language_id, total_questions, 
              datetime.utcnow(), json.dumps(resume_data)))
        
        attempt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'attempt_id': attempt_id,
            'book_id': book_id,
            'level_id': level_id,
            'language_id': language_id,
            'total_questions': total_questions,
            'current_question_number': 1,
            'status': 'in_progress'
        }
    
    def get_next_question(self, attempt_id: int, user_id: int) -> Dict:
        """Get the next question for the quiz"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get quiz attempt
        cursor.execute("""
            SELECT id, user_id, total_questions, status, resume_data
            FROM quiz_attempts 
            WHERE id = ? AND user_id = ?
        """, (attempt_id, user_id))
        
        attempt = cursor.fetchone()
        
        if not attempt:
            conn.close()
            return {'error': 'Quiz attempt not found'}
        
        if attempt['status'] != 'in_progress':
            conn.close()
            return {'error': 'Quiz already completed'}
        
        # Parse resume data
        resume_data = json.loads(attempt['resume_data'])
        question_ids = resume_data['question_ids']
        current_index = resume_data['current_index']
        
        # Check if quiz is complete
        if current_index >= len(question_ids):
            conn.close()
            return {'completed': True, 'message': 'Quiz completed'}
        
        # Get the next question
        question_id = question_ids[current_index]
        language_id = resume_data.get('language_id')
        
        cursor.execute("""
            SELECT q.id as question_id, qt.text as question, q.verse_reference
            FROM questions q
            JOIN question_texts qt ON qt.question_id = q.id
            WHERE q.id = ? AND qt.language_id = ?
        """, (question_id, language_id))
        
        question = cursor.fetchone()
        
        if not question:
            conn.close()
            return {'error': 'Question not found'}
        
        # Get options
        cursor.execute("""
            SELECT o.label, ot.text as option_text
            FROM options o
            JOIN option_texts ot ON ot.option_id = o.id
            WHERE o.question_id = ? AND ot.language_id = ?
            ORDER BY o.label
        """, (question_id, language_id))
        
        options = [{'label': row['label'], 'text': row['option_text']} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'attempt_id': attempt_id,
            'question_number': current_index + 1,
            'remaining_questions': len(question_ids) - current_index - 1,
            'question': {
                'question_id': question['question_id'],
                'text': question['question'],
                'verse_reference': question['verse_reference'],
                'options': options
            }
        }
    
    def submit_answer(self, attempt_id: int, user_id: int, question_id: int, selected_option: str) -> Dict:
        """Submit an answer and move to next question"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get quiz attempt
        cursor.execute("""
            SELECT id, user_id, total_questions, status, resume_data
            FROM quiz_attempts 
            WHERE id = ? AND user_id = ?
        """, (attempt_id, user_id))
        
        attempt = cursor.fetchone()
        
        if not attempt:
            conn.close()
            return {'error': 'Quiz attempt not found'}
        
        if attempt['status'] != 'in_progress':
            conn.close()
            return {'error': 'Quiz already completed'}
        
        # Parse resume data
        resume_data = json.loads(attempt['resume_data'])
        question_ids = resume_data['question_ids']
        current_index = resume_data['current_index']
        
        # Verify this is the expected question
        expected_question_id = question_ids[current_index]
        if expected_question_id != question_id:
            conn.close()
            return {'error': 'Question out of order'}
        
        # Get question details
        language_id = resume_data.get('language_id')
        
        cursor.execute("""
            SELECT q.correct_option, q.verse_reference
            FROM questions q
            WHERE q.id = ?
        """, (question_id,))
        
        question = cursor.fetchone()
        
        if not question:
            conn.close()
            return {'error': 'Question not found'}
        
        # Check if answer is correct
        is_correct = (selected_option == question['correct_option'])
        
        # Get correct option text
        cursor.execute("""
            SELECT ot.text
            FROM options o
            JOIN option_texts ot ON ot.option_id = o.id
            WHERE o.question_id = ? AND o.label = ? AND ot.language_id = ?
        """, (question_id, question['correct_option'], language_id))
        
        correct_text_row = cursor.fetchone()
        correct_text = correct_text_row['text'] if correct_text_row else question['correct_option']
        
        # Get explanation
        cursor.execute("""
            SELECT text FROM explanations 
            WHERE question_id = ? AND language_id = ?
        """, (question_id, language_id))
        
        explanation_row = cursor.fetchone()
        explanation = explanation_row['text'] if explanation_row else ""
        
        # Get verse text
        verse_text = self._get_verse_text(question['verse_reference'], language_id)
        
        # Save answer
        cursor.execute("""
            INSERT INTO quiz_answers (attempt_id, question_id, selected_option, is_correct)
            VALUES (?, ?, ?, ?)
        """, (attempt_id, question_id, selected_option, is_correct))
        
        # Update resume data
        resume_data['current_index'] = current_index + 1
        resume_data['answers'].append({
            'question_id': question_id,
            'selected_option': selected_option,
            'is_correct': is_correct
        })
        
        # Update attempt
        new_answered = current_index + 1
        correct_count = sum(1 for a in resume_data['answers'] if a['is_correct'])
        
        cursor.execute("""
            UPDATE quiz_attempts 
            SET answered_questions = ?, correct_answers = ?, resume_data = ?
            WHERE id = ?
        """, (new_answered, correct_count, json.dumps(resume_data), attempt_id))
        
        conn.commit()
        
        # Check if quiz is complete
        is_complete = (new_answered >= attempt['total_questions'])
        next_available = not is_complete
        
        result = {
            'is_correct': is_correct,
            'selected_option': selected_option,
            'correct_option': {
                'label': question['correct_option'],
                'text': correct_text
            },
            'verse_reference': question['verse_reference'],
            'explanation': explanation,
            'progress': {
                'current': new_answered,
                'total': attempt['total_questions'],
                'remaining': attempt['total_questions'] - new_answered
            },
            'next_available': next_available
        }
        
        conn.close()
        return result
    
    def finish_quiz(self, attempt_id: int, user_id: int) -> Dict:
        """Finish the quiz and calculate final score"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get quiz attempt
        cursor.execute("""
            SELECT id, total_questions, correct_answers, status
            FROM quiz_attempts 
            WHERE id = ? AND user_id = ?
        """, (attempt_id, user_id))
        
        attempt = cursor.fetchone()
        
        if not attempt:
            conn.close()
            return {'error': 'Quiz attempt not found'}
        
        if attempt['status'] == 'completed':
            conn.close()
            return {'error': 'Quiz already completed'}
        
        # Calculate final score
        total_questions = attempt['total_questions']
        correct_answers = attempt['correct_answers'] or 0
        wrong_answers = total_questions - correct_answers
        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Update attempt as completed
        cursor.execute("""
            UPDATE quiz_attempts 
            SET status = 'completed', 
                completed_at = ?,
                score_percentage = ?
            WHERE id = ?
        """, (datetime.utcnow(), score_percentage, attempt_id))
        
        # Update user statistics
        cursor.execute("""
            UPDATE users 
            SET total_quizzes_taken = total_quizzes_taken + 1,
                total_questions_answered = total_questions_answered + ?,
                total_correct_answers = total_correct_answers + ?,
                updated_at = ?
            WHERE id = ?
        """, (total_questions, correct_answers, datetime.utcnow(), user_id))
        
        conn.commit()
        conn.close()
        
        return {
            'attempt_id': attempt_id,
            'score_percentage': round(score_percentage, 2),
            'correct_answers': correct_answers,
            'wrong_answers': wrong_answers,
            'total_questions': total_questions,
            'status': 'completed'
        }
    
    def get_quiz_review(self, attempt_id: int, user_id: int) -> Dict:
        """Get full quiz review with all questions and answers"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get quiz attempt
        cursor.execute("""
            SELECT id, total_questions, correct_answers, score_percentage, status, resume_data
            FROM quiz_attempts 
            WHERE id = ? AND user_id = ?
        """, (attempt_id, user_id))
        
        attempt = cursor.fetchone()
        
        if not attempt:
            conn.close()
            return {'error': 'Quiz attempt not found'}
        
        # Get all answers
        cursor.execute("""
            SELECT question_id, selected_option, is_correct
            FROM quiz_answers 
            WHERE attempt_id = ?
            ORDER BY id
        """, (attempt_id,))
        
        answers = {row['question_id']: row for row in cursor.fetchall()}
        
        # Get all questions from resume_data
        resume_data = json.loads(attempt['resume_data']) if attempt['resume_data'] else {}
        question_ids = resume_data.get('question_ids', [])
        language_id = resume_data.get('language_id', 1)
        
        # Build review data
        review_questions = []
        
        for qid in question_ids:
            cursor.execute("""
                SELECT q.correct_option, q.verse_reference, qt.text as question_text
                FROM questions q
                JOIN question_texts qt ON qt.question_id = q.id
                WHERE q.id = ? AND qt.language_id = ?
            """, (qid, language_id))
            
            question = cursor.fetchone()
            
            if not question:
                continue
            
            answer = answers.get(qid)
            selected = answer['selected_option'] if answer else None
            is_correct = answer['is_correct'] if answer else False
            
            # Get explanation
            cursor.execute("""
                SELECT text FROM explanations 
                WHERE question_id = ? AND language_id = ?
            """, (qid, language_id))
            
            explanation_row = cursor.fetchone()
            explanation = explanation_row['text'] if explanation_row else ""
            
            review_questions.append({
                'question_id': qid,
                'question': question['question_text'],
                'selected_option': selected,
                'correct_option': question['correct_option'],
                'is_correct': is_correct,
                'verse_reference': question['verse_reference'],
                'explanation': explanation
            })
        
        conn.close()
        
        total_questions = attempt['total_questions']
        correct_answers = attempt['correct_answers'] or 0
        wrong_answers = total_questions - correct_answers
        
        return {
            'attempt_id': attempt_id,
            'summary': {
                'score_percentage': round(attempt['score_percentage'] or 0, 2),
                'correct_answers': correct_answers,
                'wrong_answers': wrong_answers,
                'total_questions': total_questions
            },
            'questions': review_questions
        }
    
    def _get_verse_text(self, reference: str, language_id: int) -> str:
        """Get verse text from reference using language ID"""
        if not reference:
            return ""
        
        match = re.match(r'([\w\s]+)\s+(\d+):(\d+)', reference)
        if not match:
            return ""
        
        book_name = match.group(1).strip()
        chapter = int(match.group(2))
        verse = int(match.group(3))
        
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT vt.text
            FROM books b
            JOIN chapters c ON c.book_id = b.id
            JOIN verses v ON v.chapter_id = c.id
            JOIN verse_texts vt ON vt.verse_id = v.id
            WHERE b.name LIKE ? AND c.chapter_number = ? 
              AND v.verse_number = ? AND vt.language_id = ?
        """, (f'%{book_name}%', chapter, verse, language_id))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['text'] if result else ""