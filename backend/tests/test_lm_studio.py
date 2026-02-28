import asyncio
import httpx
import os
import sys

# Add backend to path so we can import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.ai_provider import LMStudioProvider

async def test_lm_studio_direct():
    """Test LM Studio directly using the provider's diagnostic method."""
    print("\n=== LM Studio Connectivity Test ===")
    
    provider = LMStudioProvider()
    print(f"Testing URL: {provider.base_url}")
    print(f"Testing Model: {provider.model_name}")
    
    # 1. Check basic availability
    available = provider.is_available()
    print(f"Is Available (basic check): {available}")
    
    # 2. Run detailed diagnostic
    print("\nRunning detailed diagnostic...")
    results = await provider.test_connectivity()
    
    for key, value in results.items():
        status = "✅" if value is True else "❌" if value is False else ""
        print(f"{status} {key}: {value}")
    
    if results.get("response_generated"):
        print("\n✅ SUCCESS: LM Studio is working correctly!")
    else:
        print("\n❌ FAILURE: Could not get a response from LM Studio.")
        if results.get("error"):
            print(f"Error detail: {results['error']}")

if __name__ == "__main__":
    asyncio.run(test_lm_studio_direct())
