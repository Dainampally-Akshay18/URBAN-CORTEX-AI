import asyncio
import sys
from unittest.mock import MagicMock, patch

# Add the project root to sys.path
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock BaseRepository BEFORE importing service to avoid google-cloud-firestore import errors
from unittest.mock import MagicMock
import sys

mock_repo = MagicMock()
sys.modules["app.repositories.base_repository"] = MagicMock(BaseRepository=MagicMock(return_value=mock_repo))

from app.services.operations_Assistant_service import OperationsAssistantService

async def test_assistant_logic():
    print("Testing AI Assistant Logic...")
    service = OperationsAssistantService()
    
    # 1. Test Intent Detection
    print("\n1. Testing Intent Detection:")
    questions = [
        ("Which bins are full?", "overflow_monitoring"),
        ("How many complaints?", "complaint_tracking"),
        ("Which truck has the longest route?", "route_analytics"),
        ("Why was B102 prioritized?", "operational_explanation"),
    ]
    
    for q, expected in questions:
        detected = service._detect_intent(q)
        print(f"  Q: '{q}' -> Intent: {detected} (Expected: {expected})")
        
    # 2. Test Context Building with Mock Data
    print("\n2. Testing Context Building:")
    mock_data = {
        "bins": [{"bin_id": "B104", "fill_level": 92, "status": "urgent", "time_to_overflow_minutes": 72}],
        "complaints": [{"type": "Overflow", "description": "Bin B104 is messy", "city": "Mumbai"}]
    }
    context = service._build_context(mock_data)
    print("  Built Context:")
    print(context)
    
    # 3. Test LLM Flow (Mocked API call)
    print("\n3. Testing LLM Integration (Mocked):")
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Mocked AI Response"}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        service.settings.groq_api_key = "test_key"
        result = await service.query_assistant("What is happening with B104?")
        print(f"  AI Answer: {result['answer']}")
        print(f"  Intent: {result['intent_detected']}")

if __name__ == "__main__":
    asyncio.run(test_assistant_logic())
