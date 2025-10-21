#!/usr/bin/env python3
"""
Re-process Candidate with Improved Extraction
Re-extracts contact info using the improved dynamic algorithm
"""
import asyncio
import sys
import os

# Add the app directory to Python path  
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import connect_to_mongo, get_database
from app.services.ai_service import AIService

async def reprocess_candidate():
    """Re-process candidate with improved extraction."""
    print("🔄 Re-processing Candidate with Improved Extraction")
    print("=" * 60)
    
    # Connect to database
    await connect_to_mongo()
    db = get_database()
    
    # Initialize AI service
    ai_service = AIService()
    
    # Find candidate with pkparthkothari email
    candidate = await db.candidates.find_one({
        "email": "pkparthkothari@gmail.com"
    })
    
    if candidate:
        print(f"Found candidate: {candidate['name']}")
        
        # Get the extracted text if available
        extracted_text = candidate.get('extractedText', '')
        
        if extracted_text:
            print("Re-extracting contact info from stored text...")
            
            # Re-extract contact info with improved algorithm
            contact_info = ai_service._extract_contact_info(extracted_text)
            
            print(f"New extraction results:")
            print(f"  Name: {contact_info.get('name', 'NOT FOUND')}")
            print(f"  Email: {contact_info.get('email', 'NOT FOUND')}")
            print(f"  Phone: {contact_info.get('phone', 'NOT FOUND')}")
            print(f"  LinkedIn: {contact_info.get('linkedin', 'NOT FOUND')}")
            print(f"  GitHub: {contact_info.get('github', 'NOT FOUND')}")
            print(f"  Location: {contact_info.get('location', 'NOT FOUND')}")
            
            # Update candidate with improved extraction
            update_data = {}
            if contact_info.get('name'):
                update_data['name'] = contact_info['name']
            if contact_info.get('linkedin'):
                update_data['linkedin'] = contact_info['linkedin']
            if contact_info.get('github'):
                update_data['github'] = contact_info['github']
            if contact_info.get('location'):
                update_data['location'] = contact_info['location']
            
            if update_data:
                result = await db.candidates.update_one(
                    {"email": "pkparthkothari@gmail.com"},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    print(f"\n✅ Updated candidate with improved extraction")
                    print(f"   Updated fields: {list(update_data.keys())}")
                else:
                    print(f"\n⚠️  No changes needed")
        else:
            print("❌ No extracted text found for candidate")
    else:
        print("❌ Candidate not found")

if __name__ == "__main__":
    asyncio.run(reprocess_candidate())