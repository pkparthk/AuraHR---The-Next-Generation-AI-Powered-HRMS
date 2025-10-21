#!/usr/bin/env python3
"""
Fix Incorrect Candidate Name
Updates the candidate with wrong name to correct name
"""
import asyncio
import sys
import os

# Add the app directory to Python path  
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import connect_to_mongo, get_database

async def fix_candidate_name():
    """Fix the incorrect candidate name."""
    print("🔧 Fixing Incorrect Candidate Name")
    print("=" * 50)
    
    # Connect to database
    await connect_to_mongo()
    db = get_database()
    
    # Find candidate with incorrect name but correct email
    incorrect_candidate = await db.candidates.find_one({
        "email": "pkparthkothari@gmail.com"
    })
    
    if incorrect_candidate:
        print(f"Found candidate with incorrect name: '{incorrect_candidate['name']}'")
        
        # Update with correct name
        result = await db.candidates.update_one(
            {"email": "pkparthkothari@gmail.com"},
            {"$set": {"name": "Parth Kothari"}}
        )
        
        if result.modified_count > 0:
            print("✅ Successfully updated name to 'Parth Kothari'")
        else:
            print("❌ Failed to update name")
    else:
        print("❌ Candidate not found")
    
    # Verify the fix
    updated_candidate = await db.candidates.find_one({
        "email": "pkparthkothari@gmail.com"
    })
    
    if updated_candidate:
        print(f"\nVerification - Updated candidate:")
        print(f"  Name: {updated_candidate['name']}")
        print(f"  Email: {updated_candidate['email']}")

if __name__ == "__main__":
    asyncio.run(fix_candidate_name())