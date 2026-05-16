# scripts/test_genesis_complete.py
"""
Complete working test for Genesis Quiz
Run: python test_genesis_complete.py
"""

import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def extract_data(response):
    """Extract data from response that might be in tuple format"""
    try:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return data
    except:
        return {}

def test_genesis_quiz():
    print("\n" + "🎯"*30)
    print("GENESIS QUIZ TEST")
    print("🎯"*30)
    
    # Step 1: Register a new user
    print("\n" + "="*60)
    print("STEP 1: REGISTER USER")
    print("="*60)
    
    username = "genesis_test_user"
    email = "genesistest@example.com"
    password = "test123"
    
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"Register Status: {response.status_code}")
    
    resp_data = extract_data(response)
    if resp_data.get('status') == 'success':
        print(f"✅ User registered: {username}")
    else:
        print(f"⚠️ User may already exist: {resp_data.get('message')}")
    
    # Step 2: Login
    print("\n" + "="*60)
    print("STEP 2: LOGIN")
    print("="*60)
    
    login_data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"Login Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    resp_data = extract_data(response)
    token = resp_data.get('data', {}).get('access_token')
    if not token:
        token = resp_data.get('access_token')
    
    if not token:
        print("❌ No token received")
        print(f"Response: {resp_data}")
        return
    
    print(f"✅ Login successful!")
    print(f"   Token: {token[:50]}...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Step 3: Get books
    print("\n" + "="*60)
    print("STEP 3: GET BOOKS")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/quiz/books", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get books: {response.status_code}")
        return
    
    resp_data = extract_data(response)
    books = resp_data.get('data', [])
    print(f"Found {len(books)} books")
    
    # Find Genesis
    genesis_book = None
    for book in books:
        if book.get('name') == 'Genesis':
            genesis_book = book
            break
    
    if not genesis_book:
        print("❌ Genesis not found")
        for book in books[:5]:
            print(f"   - {book.get('name')} (ID: {book.get('book_id')})")
        return
    
    book_id = genesis_book.get('book_id')
    print(f"✅ Found Genesis (ID: {book_id})")
    print(f"   Total questions: {genesis_book.get('total_questions')}")
    for level in genesis_book.get('levels', []):
        print(f"   Level {level.get('level_id')}: {level.get('name')} - {level.get('question_count')} questions")
    
    # Step 4: Start quiz
    print("\n" + "="*60)
    print("STEP 4: START QUIZ")
    print("="*60)
    
    start_data = {
        "book_id": book_id,
        "level_id": 1,
        "language_id": 1
    }
    
    response = requests.post(f"{BASE_URL}/api/quiz/quiz/start", json=start_data, headers=headers)
    
    if response.status_code != 201:
        print(f"❌ Failed to start quiz: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    result = extract_data(response)
    attempt_id = result.get('data', {}).get('attempt_id')
    total_questions = result.get('data', {}).get('total_questions')
    
    print(f"✅ Quiz started!")
    print(f"   Attempt ID: {attempt_id}")
    print(f"   Total questions: {total_questions}")
    
    # Step 5: Answer questions
    print("\n" + "="*60)
    print("STEP 5: ANSWER QUESTIONS")
    print("="*60)
    
    for i in range(min(3, total_questions)):
        print(f"\n--- Question {i+1} ---")
        
        # Get next question
        response = requests.get(f"{BASE_URL}/api/quiz/quiz/{attempt_id}/next", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to get question: {response.status_code}")
            break
        
        q_result = extract_data(response)
        q_data = q_result.get('data', {})
        
        if q_data.get('completed'):
            print("🏁 Quiz completed!")
            break
        
        question = q_data.get('question', {})
        question_id = question.get('question_id')
        question_text = question.get('text', '')
        options = question.get('options', [])
        
        print(f"Q: {question_text[:80]}...")
        print(f"Verse: {question.get('verse_reference')}")
        print(f"Options: {len(options)}")
        
        if not options:
            print("⚠️ No options, submitting default")
            if question_id:
                answer_data = {
                    "attempt_id": attempt_id,
                    "question_id": question_id,
                    "selected_option": "A"
                }
                requests.post(f"{BASE_URL}/api/quiz/quiz/answer", json=answer_data, headers=headers)
            continue
        
        # Show first 2 options
        for opt in options[:2]:
            print(f"   {opt.get('label')}: {opt.get('text', '')[:50]}...")
        
        # Select first option
        selected = options[0].get('label')
        print(f"\n📝 Answering: {selected}")
        
        # Submit answer
        answer_data = {
            "attempt_id": attempt_id,
            "question_id": question_id,
            "selected_option": selected
        }
        
        response = requests.post(f"{BASE_URL}/api/quiz/quiz/answer", json=answer_data, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code}")
            break
        
        a_result = extract_data(response)
        a_data = a_result.get('data', {})
        
        status = "✅ CORRECT" if a_data.get('is_correct') else "❌ INCORRECT"
        print(f"   {status}")
        
        progress = a_data.get('progress', {})
        print(f"   Progress: {progress.get('current')}/{progress.get('total')}")
        
        time.sleep(0.5)
    
    # Step 6: Finish quiz
    print("\n" + "="*60)
    print("STEP 6: FINISH QUIZ")
    print("="*60)
    
    response = requests.post(f"{BASE_URL}/api/quiz/quiz/{attempt_id}/finish", headers=headers)
    
    if response.status_code == 200:
        f_result = extract_data(response)
        f_data = f_result.get('data', {})
        print(f"✅ Quiz completed!")
        print(f"   Score: {f_data.get('score_percentage')}%")
        print(f"   Correct: {f_data.get('correct_answers')}/{f_data.get('total_questions')}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Step 7: Get review
    print("\n" + "="*60)
    print("STEP 7: QUIZ REVIEW")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/quiz/quiz/{attempt_id}/review", headers=headers)
    
    if response.status_code == 200:
        r_result = extract_data(response)
        r_data = r_result.get('data', {})
        summary = r_data.get('summary', {})
        print(f"Review Score: {summary.get('score_percentage')}%")
        print(f"Total: {summary.get('total_questions')} questions")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    print("\n" + "🎯"*30)
    print("✅ TEST COMPLETE!")
    print("🎯"*30)

if __name__ == "__main__":
    test_genesis_quiz()