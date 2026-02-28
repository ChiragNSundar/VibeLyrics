import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.ai_provider import LMStudioProvider, GHOSTWRITER_SYSTEM_INSTRUCTION

async def debug_improvement():
    try:
        provider = LMStudioProvider()
        original_line = "I'm walking down the street"
        improvement_type = "rhyme"
        
        print(f"Testing improvement for: '{original_line}'")
        print(f"Type: {improvement_type}")
        
        improved = await provider.improve_line(original_line, improvement_type)
        
        print(f"\nResult: '{improved}'")
        
        if improved == original_line:
            print("\n❌ FAILURE: AI returned the exact same line.")
        else:
            print("\n✅ SUCCESS: AI improved the line!")
    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_improvement())
