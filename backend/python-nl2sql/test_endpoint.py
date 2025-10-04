#!/usr/bin/env python3
"""
Test script for the file upload endpoint
"""
import requests
import uuid
import os

def test_file_upload():
    """Test the file upload endpoint with the student CSV file"""
    
    # Use the existing CSV file
    csv_file_path = "/home/balaji/Projects/chatbot/backend/python-nl2sql/student-por.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"CSV file not found: {csv_file_path}")
        return
    
    # Generate test UUIDs
    chat_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    # Prepare the request
    url = f"http://localhost:8000/chats/{chat_id}/files"
    
    with open(csv_file_path, 'rb') as f:
        files = {'file': ('student-por.csv', f, 'text/csv')}
        data = {'user_id': user_id}
        
        try:
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                print(f"File ID: {result['file_id']}")
                print(f"Filename: {result['filename']}")
                print(f"Table Name: {result['table_name']}")
                print(f"Number of columns in metadata: {len(result['columns_metadata'])}")
                print(f"SQL Schema length: {len(result['sql_schema'])} characters")
                
                # Print first few columns metadata
                print("\nFirst 3 columns metadata:")
                for i, col in enumerate(result['columns_metadata'][:3]):
                    print(f"  {i+1}. {col['column_name']} ({col['data_type']}) - Unique: {col['unique_count']}")
                    
            else:
                print(f"❌ Upload failed with status {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing file upload endpoint...")
    test_file_upload()