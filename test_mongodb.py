#!/usr/bin/env python3
"""
MongoDB Connection Test Script
Run this to test your MongoDB Atlas connection
"""

from pymongo import MongoClient
import urllib.parse

def test_mongodb_connection():
    try:
        print("🔄 Testing MongoDB Atlas connection...")
        
        # Method 1: Direct connection string
        print("\n📝 Method 1: Direct connection")
        connection_string = "mongodb+srv://Natesh:Natesh@cluster0.wwp3oig.mongodb.net/?retryWrites=true&w=majority"
        
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        
        # Test the connection
        client.admin.command('ping')
        print("✅ Method 1: SUCCESS - Connected to MongoDB Atlas!")
        
        # Test database operations
        db = client.cms_database
        
        # Insert a test document
        test_collection = db.test_collection
        result = test_collection.insert_one({"test": "connection", "status": "working"})
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Read the test document
        doc = test_collection.find_one({"test": "connection"})
        print(f"✅ Test document retrieved: {doc}")
        
        # Clean up test document
        test_collection.delete_one({"_id": result.inserted_id})
        print("✅ Test document cleaned up")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
        
        # Method 2: URL encoded credentials
        try:
            print("\n📝 Method 2: URL encoded credentials")
            username = urllib.parse.quote_plus('Natesh')
            password = urllib.parse.quote_plus('Natesh')
            
            connection_string = f"mongodb+srv://{username}:{password}@cluster0.wwp3oig.mongodb.net/?retryWrites=true&w=majority"
            
            client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            print("✅ Method 2: SUCCESS - Connected with URL encoding!")
            client.close()
            return True
            
        except Exception as e2:
            print(f"❌ Method 2 failed: {e2}")
            
            # Method 3: Alternative parameters
            try:
                print("\n📝 Method 3: Alternative SSL settings")
                client = MongoClient(
                    "mongodb+srv://Natesh:Natesh@cluster0.wwp3oig.mongodb.net/",
                    tlsAllowInvalidCertificates=True,
                    serverSelectionTimeoutMS=5000
                )
                client.admin.command('ping')
                print("✅ Method 3: SUCCESS - Connected with SSL bypass!")
                client.close()
                return True
                
            except Exception as e3:
                print(f"❌ Method 3 failed: {e3}")
                return False

def print_troubleshooting_tips():
    print("\n🔧 TROUBLESHOOTING TIPS:")
    print("1. Check Network Access in MongoDB Atlas:")
    print("   - Go to Network Access → Add IP Address → Allow Access from Anywhere (0.0.0.0/0)")
    print("\n2. Verify Database User:")
    print("   - Go to Database Access → Check if user 'Natesh' exists with password 'Natesh'")
    print("   - User should have 'Read and write to any database' privileges")
    print("\n3. Check Cluster Status:")
    print("   - Go to Clusters → Ensure cluster is running (not paused)")
    print("\n4. Firewall/Antivirus:")
    print("   - Temporarily disable firewall/antivirus to test connection")
    print("\n5. Internet Connection:")
    print("   - Ensure stable internet connection")

if __name__ == "__main__":
    print("🚀 MongoDB Atlas Connection Test")
    print("=" * 50)
    
    success = test_mongodb_connection()
    
    if not success:
        print_troubleshooting_tips()
        print("\n❌ All connection methods failed!")
        print("Please follow the troubleshooting tips above.")
    else:
        print("\n🎉 MongoDB Atlas connection is working!")
        print("You can now run your Flask application.")