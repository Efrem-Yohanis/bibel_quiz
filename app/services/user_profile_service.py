# app/services/user_profile_service.py
"""
User Profile Service - Manages user quiz history, progress, and resume functionality
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

DB_PATH = Path(__file__).parent.parent / 'bible_quiz.db'

class UserProfileService:
    """Service for managing user profiles, quiz history, and progress"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def get_db(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_user_complete_profile(self, user_id: int) -> Dict[str, Any]:
        """Get complete user profile with all history and progress"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get basic user info
        cursor.execute("""
            SELECT id, username, email, created_at, last_login,
                   total_quizzes_taken, total_correct_answers, total_questions_answered,
                   is_active
            FROM users WHERE id = ?
        """, (user_id,))
        
        user = cursor.fetchone()
        if not user:
            conn.close()
            return {'error': 'User not found'}
        
        # Calculate accuracy
        accuracy = 0
        if user['total_questions_answered'] > 0:
            accuracy = (user['total_correct_answers'] / user['total_questions_answered']) * 100
        
        # Get quiz history
        quiz_history = self.get_quiz_history(user_id, conn)
        
        # Get in-progress quizzes
        in_progress_quizzes = self.get_in_progress_quizzes(user_id, conn)
        
        # Get book progress
        book_progress = self.get_book_progress(user_id, conn)
        
        # Get recent activity
        recent_activity = self.get_recent_activity(user_id, conn)
        
        conn.close()
        
        return {
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'member_since': user['created_at'],
                'last_login': user['last_login'],
                'is_active': user['is_active']
            },
            'statistics': {
                'total_quizzes_taken': user['total_quizzes_taken'] or 0,
                'total_questions_answered': user['total_questions_answered'] or 0,
                'total_correct_answers': user['total_correct_answers'] or 0,
                'accuracy_percentage': round(accuracy, 2)
            },
            'quiz_history': quiz_history,
            'in_progress_quizzes': in_progress_quizzes,
            'book_progress': book_progress,
            'recent_activity': recent_activity,
            'can_resume': len(in_progress_quizzes) > 0
        }
    
    def get_quiz_history(self, user_id: int, conn=None) -> List[Dict]:
        """Get user's quiz history"""
        close_conn = False
        if conn is None:
            conn = self.get_db()
            close_conn = True
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, book_name, testament, total_questions, answered_questions,
                   correct_answers, score_percentage, status, started_at, completed_at
            FROM quiz_attempts 
            WHERE user_id = ? AND status = 'completed'
            ORDER BY completed_at DESC
            LIMIT 50
        """, (user_id,))
        
        history = [dict(row) for row in cursor.fetchall()]
        
        if close_conn:
            conn.close()
        
        return history
    
    def get_in_progress_quizzes(self, user_id: int, conn=None) -> List[Dict]:
        """Get quizzes that are in progress (can be resumed)"""
        close_conn = False
        if conn is None:
            conn = self.get_db()
            close_conn = True
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, book_name, testament, total_questions, answered_questions,
                   correct_answers, last_question_index, started_at, resume_data
            FROM quiz_attempts 
            WHERE user_id = ? AND status = 'in_progress'
            ORDER BY started_at DESC
        """, (user_id,))
        
        quizzes = []
        for row in cursor.fetchall():
            quiz = dict(row)
            # Parse resume data if exists
            if quiz.get('resume_data'):
                try:
                    quiz['resume_data'] = json.loads(quiz['resume_data'])
                except:
                    quiz['resume_data'] = None
            quizzes.append(quiz)
        
        if close_conn:
            conn.close()
        
        return quizzes
    
    def get_book_progress(self, user_id: int, conn=None) -> List[Dict]:
        """Get user's progress through each book"""
        close_conn = False
        if conn is None:
            conn = self.get_db()
            close_conn = True
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT book_name, testament, current_chapter, current_verse,
                   questions_answered, correct_answers, last_activity, completed
            FROM user_book_progress 
            WHERE user_id = ?
            ORDER BY testament, book_name
        """, (user_id,))
        
        progress = [dict(row) for row in cursor.fetchall()]
        
        if close_conn:
            conn.close()
        
        return progress
    
    def get_recent_activity(self, user_id: int, conn=None, limit: int = 20) -> List[Dict]:
        """Get recent user activity"""
        close_conn = False
        if conn is None:
            conn = self.get_db()
            close_conn = True
        
        cursor = conn.cursor()
        
        # Get recent quiz completions
        cursor.execute("""
            SELECT 'quiz_completed' as activity_type, book_name, score_percentage,
                   completed_at as activity_date
            FROM quiz_attempts 
            WHERE user_id = ? AND status = 'completed'
            ORDER BY completed_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        activities = [dict(row) for row in cursor.fetchall()]
        
        if close_conn:
            conn.close()
        
        return activities
    
    def start_new_quiz(self, user_id: int, book_name: str, testament: str, 
                      total_questions: int) -> Dict:
        """Start a new quiz session"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO quiz_attempts (user_id, book_name, testament, total_questions, 
                                       status, started_at, last_question_index)
            VALUES (?, ?, ?, ?, 'in_progress', ?, 0)
        """, (user_id, book_name, testament, total_questions, datetime.utcnow()))
        
        attempt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'attempt_id': attempt_id,
            'book_name': book_name,
            'testament': testament,
            'total_questions': total_questions,
            'status': 'in_progress',
            'started_at': datetime.utcnow().isoformat()
        }
    
    def save_quiz_answer(self, attempt_id: int, question_data: Dict) -> bool:
        """Save an answer for a quiz"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # Save the answer
            cursor.execute("""
                INSERT INTO quiz_answers (attempt_id, question_id, question_text, 
                                          selected_option, is_correct, correct_option, 
                                          explanation, answered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                attempt_id,
                question_data.get('question_id'),
                question_data.get('question_text'),
                question_data.get('selected_option'),
                question_data.get('is_correct'),
                question_data.get('correct_option'),
                question_data.get('explanation'),
                datetime.utcnow()
            ))
            
            # Update attempt statistics
            cursor.execute("""
                UPDATE quiz_attempts 
                SET answered_questions = answered_questions + 1,
                    correct_answers = correct_answers + ?,
                    last_question_index = last_question_index + 1,
                    score_percentage = (correct_answers + ?) * 100.0 / total_questions
                WHERE id = ?
            """, (1 if question_data.get('is_correct') else 0, 
                  1 if question_data.get('is_correct') else 0,
                  attempt_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error saving answer: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def complete_quiz(self, attempt_id: int) -> Dict:
        """Mark a quiz as completed and update user stats"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get attempt details
        cursor.execute("""
            SELECT user_id, correct_answers, total_questions, score_percentage, book_name
            FROM quiz_attempts WHERE id = ?
        """, (attempt_id,))
        
        attempt = cursor.fetchone()
        
        if not attempt:
            conn.close()
            return {'error': 'Attempt not found'}
        
        # Update attempt as completed
        cursor.execute("""
            UPDATE quiz_attempts 
            SET status = 'completed', completed_at = ?
            WHERE id = ?
        """, (datetime.utcnow(), attempt_id))
        
        # Update user statistics
        cursor.execute("""
            UPDATE users 
            SET total_quizzes_taken = total_quizzes_taken + 1,
                total_questions_answered = total_questions_answered + ?,
                total_correct_answers = total_correct_answers + ?,
                updated_at = ?
            WHERE id = ?
        """, (attempt['total_questions'], attempt['correct_answers'], 
              datetime.utcnow(), attempt['user_id']))
        
        conn.commit()
        
        # Get updated stats
        cursor.execute("""
            SELECT score_percentage, correct_answers, total_questions
            FROM quiz_attempts WHERE id = ?
        """, (attempt_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'success': True,
            'score_percentage': result['score_percentage'],
            'correct_answers': result['correct_answers'],
            'total_questions': result['total_questions']
        }
    
    def resume_quiz(self, attempt_id: int) -> Dict:
        """Get quiz data to resume from where user stopped"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, book_name, testament, total_questions, answered_questions,
                   correct_answers, last_question_index, resume_data, started_at
            FROM quiz_attempts 
            WHERE id = ? AND status = 'in_progress'
        """, (attempt_id,))
        
        attempt = cursor.fetchone()
        
        if not attempt:
            conn.close()
            return {'error': 'No in-progress quiz found to resume'}
        
        # Get previous answers
        cursor.execute("""
            SELECT question_id, selected_option, is_correct
            FROM quiz_answers 
            WHERE attempt_id = ?
            ORDER BY answered_at
        """, (attempt_id,))
        
        previous_answers = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'attempt_id': attempt['id'],
            'book_name': attempt['book_name'],
            'testament': attempt['testament'],
            'total_questions': attempt['total_questions'],
            'answered_questions': attempt['answered_questions'],
            'correct_answers': attempt['correct_answers'],
            'last_question_index': attempt['last_question_index'],
            'progress_percentage': (attempt['answered_questions'] / attempt['total_questions']) * 100 if attempt['total_questions'] > 0 else 0,
            'previous_answers': previous_answers,
            'started_at': attempt['started_at'],
            'can_resume': True
        }
    
    def update_book_progress(self, user_id: int, book_name: str, testament: str,
                            chapter: int, verse: int) -> bool:
        """Update user's progress in a specific book"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_book_progress (user_id, book_name, testament, 
                                            current_chapter, current_verse, last_activity)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, book_name) DO UPDATE SET
                current_chapter = ?,
                current_verse = ?,
                last_activity = ?
        """, (user_id, book_name, testament, chapter, verse, datetime.utcnow(),
              chapter, verse, datetime.utcnow()))
        
        conn.commit()
        conn.close()
        
        return True