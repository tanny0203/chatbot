"""
Test script for the NL2SQL Two-Model Pipeline
Demonstrates upload, ask, and conversation flow
"""

import asyncio
import aiohttp
import json
import pandas as pd
import tempfile
import os
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"  # Sample UUID
TEST_CHAT_ID = "550e8400-e29b-41d4-a716-446655440001"  # Sample UUID

class NL2SQLTester:
    """Test client for the NL2SQL API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        async with self.session.get(f"{self.base_url}/health") as response:
            return await response.json()
    
    async def create_test_dataset(self) -> str:
        """Create a test CSV file and return the path"""
        # Create sample student marks data
        data = {
            'student_id': range(1, 21),
            'name': [f'Student_{i}' for i in range(1, 21)],
            'maths': [85, 92, 78, 88, 95, 76, 89, 91, 83, 87, 90, 82, 86, 94, 79, 85, 93, 81, 88, 92],
            'science': [88, 85, 92, 83, 89, 91, 87, 78, 95, 86, 84, 90, 82, 88, 93, 87, 85, 89, 91, 86],
            'english': [90, 87, 83, 91, 86, 88, 92, 85, 89, 93, 87, 85, 90, 83, 88, 91, 86, 92, 87, 89],
            'grade': ['A', 'A', 'B', 'A', 'A', 'B', 'A', 'A', 'B', 'A', 'A', 'B', 'A', 'A', 'B', 'A', 'A', 'A', 'A', 'A']
        }
        
        df = pd.DataFrame(data)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        return temp_file.name
    
    async def upload_dataset(self, file_path: str, filename: str = "marks.csv") -> Dict[str, Any]:
        """Upload dataset via API"""
        data = aiohttp.FormData()
        data.add_field('user_id', TEST_USER_ID)
        data.add_field('chat_id', TEST_CHAT_ID)
        
        with open(file_path, 'rb') as f:
            data.add_field('file', f, filename=filename, content_type='text/csv')
            
            async with self.session.post(f"{self.base_url}/api/upload", data=data) as response:
                result = await response.json()
                return {
                    "status_code": response.status,
                    "response": result
                }
    
    async def ask_question(self, question: str) -> Dict[str, Any]:
        """Ask a question via API"""
        payload = {
            "question": question,
            "user_id": TEST_USER_ID,
            "chat_id": TEST_CHAT_ID
        }
        
        async with self.session.post(
            f"{self.base_url}/api/ask", 
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            result = await response.json()
            return {
                "status_code": response.status,
                "response": result
            }
    
    async def get_chat_history(self) -> Dict[str, Any]:
        """Get chat history"""
        params = {"user_id": TEST_USER_ID}
        async with self.session.get(
            f"{self.base_url}/chats/{TEST_CHAT_ID}/history",
            params=params
        ) as response:
            result = await response.json()
            return {
                "status_code": response.status,
                "response": result
            }
    
    async def create_chat(self) -> Dict[str, Any]:
        """Create a new chat"""
        payload = {"user_id": TEST_USER_ID}
        async with self.session.post(
            f"{self.base_url}/chats/",
            json=payload
        ) as response:
            result = await response.json()
            return {
                "status_code": response.status,
                "response": result
            }
    
    def print_response(self, title: str, response: Dict[str, Any]):
        """Pretty print API response"""
        print(f"\n{'='*50}")
        print(f"{title}")
        print(f"{'='*50}")
        print(f"Status Code: {response['status_code']}")
        print(f"Response:")
        print(json.dumps(response['response'], indent=2, default=str))

async def run_comprehensive_test():
    """Run comprehensive test of the NL2SQL pipeline"""
    
    async with NL2SQLTester() as tester:
        print("🚀 Starting NL2SQL Two-Model Pipeline Test")
        
        # 1. Health check
        print("\n1. Health Check...")
        health = await tester.health_check()
        tester.print_response("Health Check", {"status_code": 200, "response": health})
        
        # 2. Create chat
        print("\n2. Creating Chat...")
        chat_result = await tester.create_chat()
        tester.print_response("Create Chat", chat_result)
        
        # 3. Create and upload test dataset
        print("\n3. Creating Test Dataset...")
        test_file = await tester.create_test_dataset()
        print(f"Created test file: {test_file}")
        
        print("\n4. Uploading Dataset...")
        upload_result = await tester.upload_dataset(test_file)
        tester.print_response("Upload Dataset", upload_result)
        
        # Clean up test file
        os.unlink(test_file)
        
        if upload_result["status_code"] != 200:
            print("❌ Upload failed, stopping test")
            return
        
        # 5. Test various questions
        test_questions = [
            "What are the top 5 students in maths?",
            "Show me students with maths score above 90",
            "What's the average science score?",
            "How many students got grade A?",
            "Who scored the highest in english?",
            "Show me all students with their total scores",
            "What's the distribution of grades?",
            "Find students who scored above average in all subjects"
        ]
        
        print(f"\n5. Testing {len(test_questions)} Questions...")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- Question {i}: {question} ---")
            
            result = await tester.ask_question(question)
            
            if result["status_code"] == 200:
                response = result["response"]
                print(f"✅ Success!")
                print(f"Answer: {response.get('answer', 'No answer')}")
                print(f"SQL Query: {response.get('sql_query', 'No SQL')}")
                print(f"Result Count: {response.get('result_count', 0)}")
            else:
                print(f"❌ Failed!")
                tester.print_response(f"Question {i} Failed", result)
            
            # Small delay between questions
            await asyncio.sleep(1)
        
        # 6. Get conversation history
        print("\n6. Getting Chat History...")
        history_result = await tester.get_chat_history()
        tester.print_response("Chat History", history_result)
        
        print("\n🎉 Test completed!")

async def run_simple_test():
    """Run a simple test with one question"""
    
    async with NL2SQLTester() as tester:
        print("🚀 Running Simple NL2SQL Test")
        
        # Create and upload dataset
        test_file = await tester.create_test_dataset()
        upload_result = await tester.upload_dataset(test_file)
        os.unlink(test_file)
        
        if upload_result["status_code"] == 200:
            print("✅ Dataset uploaded successfully")
            
            # Ask a question
            result = await tester.ask_question("Show me the top 3 students in maths")
            
            if result["status_code"] == 200:
                print("✅ Question processed successfully")
                print(f"Answer: {result['response'].get('answer')}")
                print(f"SQL: {result['response'].get('sql_query')}")
            else:
                print("❌ Question failed")
                print(f"Error: {result['response']}")
        else:
            print("❌ Dataset upload failed")
            print(f"Error: {upload_result['response']}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        asyncio.run(run_simple_test())
    else:
        asyncio.run(run_comprehensive_test())