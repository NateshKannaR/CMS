#!/usr/bin/env python3
"""
Local MongoDB Connection Test Script
"""

from pymongo import MongoClient

def test_local_mongodb():
    try:
        print("Testing local MongoDB connection...")
        
        # Connect to local MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        
        # Test the connection
        client.admin.command('ping')
        print("SUCCESS: Connected to local MongoDB!")
        
        # Test database operations
        db = client.cms_database
        
        # List existing collections
        collections = db.list_collection_names()
        print(f"Existing collections: {collections}")
        
        # Insert a test document
        test_collection = db.test_collection
        result = test_collection.insert_one({"test": "local_connection", "status": "working"})
        print(f"Test document inserted with ID: {result.inserted_id}")
        
        # Read the test document
        doc = test_collection.find_one({"test": "local_connection"})
        print(f"Test document retrieved: {doc}")
        
        # Clean up test document
        test_collection.delete_one({"_id": result.inserted_id})
        print("Test document cleaned up")
        
        # Show database stats
        stats = db.command("dbstats")
        print(f"Database: {stats['db']} - Collections: {stats['collections']}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Connection failed: {e}")
        print("\nTROUBLESHOOTING:")
        print("1. Make sure MongoDB is running locally")
        print("2. Check if MongoDB Compass can connect to localhost:27017")
        print("3. Verify no authentication is required")
        print("4. Try restarting MongoDB service")
        return False

if __name__ == "__main__":
    print("Local MongoDB Connection Test")
    print("=" * 40)
    
    success = test_local_mongodb()
    
    if success:
        print("\nSUCCESS: Local MongoDB connection is working!")
        print("You can now run your Flask application with: python run.py")
    else:
        print("\nERROR: Local MongoDB connection failed!")
        print("Please check your MongoDB installation and service.")