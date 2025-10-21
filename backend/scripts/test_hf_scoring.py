#!/usr/bin/env python3
"""
Test script for HuggingFace-based resume scoring system.
"""
import sys
import os
import asyncio
import glob
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.ai_service import AIService
from app.core.config import settings

async def test_hf_scoring():
    """Test the HuggingFace-based scoring system."""
    
    print("🚀 Starting HuggingFace Resume Scoring Test")
    print(f"📋 Using model: {settings.EMBEDDING_MODEL_NAME}")
    print("=" * 60)
    
    # Initialize AI service
    ai_service = AIService()
    await ai_service.initialize()
    
    # Test job description
    job_text = """
    Senior Python Backend Engineer - Remote
    
    We are seeking a highly skilled Senior Python Backend Engineer to join our dynamic team. 
    The ideal candidate will have extensive experience in developing scalable web applications 
    and APIs using modern Python frameworks.
    
    Requirements:
    - 5+ years of Python development experience
    - Strong expertise in FastAPI, Django, or Flask
    - Experience with RESTful API design and implementation
    - Knowledge of database systems (PostgreSQL, MongoDB)
    - Familiarity with cloud platforms (AWS, Azure, GCP)
    - Experience with containerization (Docker, Kubernetes)
    - Understanding of microservices architecture
    - Bachelor's degree in Computer Science or related field
    
    Preferred Skills:
    - Experience with async programming
    - Knowledge of ML/AI frameworks
    - DevOps and CI/CD pipeline experience
    - Agile development methodologies
    """
    
    # Find sample resumes in uploads folder
    uploads_dir = Path(os.path.dirname(__file__)) / ".." / "chroma_db" / "uploads"
    
    if not uploads_dir.exists():
        uploads_dir = Path(os.path.dirname(__file__)) / ".." / "uploads"
    
    resume_files = list(uploads_dir.glob("*.txt"))[:5]  # Test with first 5 resumes
    
    if not resume_files:
        print("❌ No resume files found in uploads directory")
        print(f"   Looked in: {uploads_dir}")
        return
    
    print(f"📄 Found {len(resume_files)} resume files to test")
    print()
    
    candidates = []
    
    # Load resume files
    for i, file_path in enumerate(resume_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            candidates.append({
                "id": f"candidate_{i+1}",
                "text": content,
                "filename": file_path.name
            })
            
        except Exception as e:
            print(f"⚠️  Error reading {file_path.name}: {e}")
    
    if not candidates:
        print("❌ No candidates loaded successfully")
        return
    
    try:
        # Test HuggingFace batch scoring
        print("🔄 Testing HuggingFace batch scoring...")
        hf_results = await ai_service.score_candidates_huggingface(
            job_text, 
            candidates, 
            use_classifier=False  # Test without classifier first
        )
        
        print("\n📊 HuggingFace Batch Scoring Results:")
        print("=" * 60)
        
        for result in hf_results:
            candidate = next(c for c in candidates if c["id"] == result["id"])
            print(f"📋 {candidate['filename']}")
            print(f"   Score: {result['score']:.3f}")
            print(f"   Confidence: {result['confidence']:.3f}")
            print(f"   Similarity: {result['similarity_score']:.3f}")
            print(f"   Recommendation: {result['recommendation']}")
            print()
        
        # Test individual resume scoring (with enhanced features)
        print("\n🔄 Testing individual resume scoring with enhanced features...")
        
        best_candidate = candidates[0]  # Test with first candidate
        
        detailed_score = await ai_service.calculate_resume_score(
            best_candidate["text"], 
            job_text
        )
        
        print("\n📊 Detailed Resume Analysis:")
        print("=" * 60)
        print(f"📋 File: {best_candidate['filename']}")
        print(f"📈 Overall Score: {detailed_score.get('overallScore', 'N/A')}/100")
        print(f"📄 Resume Quality: {detailed_score.get('resumeScore', 'N/A')}/100")
        print(f"🎯 Skills Match: {detailed_score.get('skillsMatch', 'N/A')}/100")
        print(f"💼 Experience Match: {detailed_score.get('experienceMatch', 'N/A')}/100")
        
        if 'semanticSimilarity' in detailed_score:
            print(f"🧠 Semantic Similarity: {detailed_score['semanticSimilarity']}/100")
        
        print(f"✅ Strengths:")
        for strength in detailed_score.get('strengths', []):
            print(f"   • {strength}")
        
        print(f"⚠️  Areas for Improvement:")
        for weakness in detailed_score.get('weaknesses', []):
            print(f"   • {weakness}")
        
        print(f"🔍 AI Insights:")
        for insight in detailed_score.get('aiInsights', []):
            print(f"   • {insight}")
        
        if 'modelUsed' in detailed_score:
            print(f"🤖 Model: {detailed_score['modelUsed']}")
        
        print(f"🎯 Recommended Action: {detailed_score.get('recommendedAction', 'N/A')}")
        
        # Performance summary
        print("\n🏆 Test Summary:")
        print("=" * 60)
        print(f"✅ Successfully processed {len(hf_results)} candidates")
        print(f"📊 Average score: {sum(r['score'] for r in hf_results) / len(hf_results):.3f}")
        print(f"📈 Score range: {min(r['score'] for r in hf_results):.3f} - {max(r['score'] for r in hf_results):.3f}")
        print(f"🤖 Model used: {settings.EMBEDDING_MODEL_NAME}")
        
        print("\n✅ HuggingFace scoring system test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_hf_scoring())