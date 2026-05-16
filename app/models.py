# app/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# 1. Language table
class Language(Base):
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False)  # 'en', 'am', 'or', 'ti'
    name = Column(String(50), nullable=False)  # 'English', 'Amharic', 'Afaan Oromo', 'Tigrinya'
    native_name = Column(String(100))  # Native name in the language itself
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    verse_texts = relationship("VerseText", back_populates="language")
    question_texts = relationship("QuestionText", back_populates="language")
    option_texts = relationship("OptionText", back_populates="language")
    explanations = relationship("Explanation", back_populates="language")

# 2. Level table (Difficulty levels)
class Level(Base):
    __tablename__ = "levels"
    
    id = Column(Integer, primary_key=True, index=True)
    level_number = Column(Integer, unique=True, nullable=False)  # 1, 2, 3
    name = Column(String(50), nullable=False)  # 'Easy', 'Medium', 'Hard'
    description = Column(Text)  # Description of the level
    icon = Column(String(50))  # Icon name or emoji
    color = Column(String(20))  # Color code for UI
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = relationship("Question", back_populates="level_ref")

# 3. Testament (Old/New)
class Testament(Base):
    __tablename__ = "testaments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)  # "Old" or "New"
    
    # Relationship
    books = relationship("Book", back_populates="testament")

# 4. Book (Genesis, Exodus, etc.)
class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    testament_id = Column(Integer, ForeignKey("testaments.id"))
    
    # Relationships
    testament = relationship("Testament", back_populates="books")
    chapters = relationship("Chapter", back_populates="book")
    questions = relationship("Question", back_populates="book")

# 5. Chapter
class Chapter(Base):
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    chapter_number = Column(Integer, nullable=False)
    
    # Relationships
    book = relationship("Book", back_populates="chapters")
    verses = relationship("Verse", back_populates="chapter")
    questions = relationship("Question", back_populates="chapter")

# 6. Verse
class Verse(Base):
    __tablename__ = "verses"
    
    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    verse_number = Column(Integer, nullable=False)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="verses")
    texts = relationship("VerseText", back_populates="verse")

# 7. Verse Text (Multi-language)
class VerseText(Base):
    __tablename__ = "verse_texts"
    
    id = Column(Integer, primary_key=True, index=True)
    verse_id = Column(Integer, ForeignKey("verses.id"))
    language_id = Column(Integer, ForeignKey("languages.id"))
    text = Column(Text, nullable=False)
    
    # Relationships
    verse = relationship("Verse", back_populates="texts")
    language = relationship("Language", back_populates="verse_texts")

# 8. Question
class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    level_id = Column(Integer, ForeignKey("levels.id"))  # Changed from level to level_id
    correct_option = Column(String(1), nullable=False)  # 'A', 'B', 'C', 'D'
    verse_reference = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    book = relationship("Book", back_populates="questions")
    chapter = relationship("Chapter", back_populates="questions")
    level_ref = relationship("Level", back_populates="questions")  # New relationship
    texts = relationship("QuestionText", back_populates="question")
    options = relationship("Option", back_populates="question")
    explanations = relationship("Explanation", back_populates="question")

# 9. Question Text (Multi-language)
class QuestionText(Base):
    __tablename__ = "question_texts"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    language_id = Column(Integer, ForeignKey("languages.id"))
    text = Column(Text, nullable=False)
    
    # Relationships
    question = relationship("Question", back_populates="texts")
    language = relationship("Language", back_populates="question_texts")

# 10. Option (A, B, C, D)
class Option(Base):
    __tablename__ = "options"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    label = Column(String(1), nullable=False)  # 'A', 'B', 'C', 'D'
    
    # Relationship
    question = relationship("Question", back_populates="options")
    texts = relationship("OptionText", back_populates="option")

# 11. Option Text (Multi-language)
class OptionText(Base):
    __tablename__ = "option_texts"
    
    id = Column(Integer, primary_key=True, index=True)
    option_id = Column(Integer, ForeignKey("options.id"))
    language_id = Column(Integer, ForeignKey("languages.id"))
    text = Column(Text, nullable=False)
    
    # Relationships
    option = relationship("Option", back_populates="texts")
    language = relationship("Language", back_populates="option_texts")

# 12. Explanation (Multi-language)
class Explanation(Base):
    __tablename__ = "explanations"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    language_id = Column(Integer, ForeignKey("languages.id"))
    text = Column(Text, nullable=False)
    
    # Relationships
    question = relationship("Question", back_populates="explanations")
    language = relationship("Language", back_populates="explanations")

# 13. Quiz Attempt
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    level_id = Column(Integer, ForeignKey("levels.id"))
    language_id = Column(Integer, ForeignKey("languages.id"))
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    score_percentage = Column(Integer, default=0)
    status = Column(String(20), default='in_progress')
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    resume_data = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="quiz_attempts")
    book = relationship("Book")
    level = relationship("Level")
    language = relationship("Language")
    answers = relationship("QuizAnswer", back_populates="attempt")

# 14. Quiz Answer
class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_option = Column(String(1), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question")

# 15. User Book Progress
class UserBookProgress(Base):
    __tablename__ = "user_book_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    current_chapter = Column(Integer, default=1)
    current_verse = Column(Integer, default=1)
    last_activity = Column(DateTime, default=datetime.utcnow)
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="book_progress")
    book = relationship("Book")

# 16. User
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    preferred_language_id = Column(Integer, ForeignKey("languages.id"), nullable=True)
    
    # Statistics
    total_quizzes_taken = Column(Integer, default=0)
    total_correct_answers = Column(Integer, default=0)
    total_questions_answered = Column(Integer, default=0)
    
    # Relationships
    preferred_language = relationship("Language")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    book_progress = relationship("UserBookProgress", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")

# 17. User Session
class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="sessions")