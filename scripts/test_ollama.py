#!/usr/bin/env python3
"""Test script for Ollama API connection.

This script verifies:
1. Connection to Ollama server
2. Text model (glm-4.7-flash or qwen2.5:7b)
3. Vision model (qwen2.5vl:7b)
"""

import asyncio
import base64
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import httpx


async def test_ollama_connection(base_url: str = "http://192.168.0.106:11434") -> bool:
    """Test basic connection to Ollama server."""
    print(f"\n🔌 Testing connection to {base_url}...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{base_url}/api/version")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Connected! Ollama version: {data.get('version', 'unknown')}")
                return True
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False


async def test_list_models(base_url: str = "http://192.168.0.106:11434") -> list[str]:
    """List available models on Ollama server."""
    print(f"\n📋 Listing available models...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                print(f"   Found {len(models)} models:")
                for m in models:
                    print(f"   - {m}")
                return models
            else:
                print(f"   ❌ Failed to list models: {response.status_code}")
                return []
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return []


async def test_text_model(
    base_url: str = "http://192.168.0.106:11434",
    model: str = "qwen2.5:7b"
) -> bool:
    """Test text model with a simple prompt."""
    print(f"\n💬 Testing text model: {model}...")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": "Say 'Hello, I am working!' in one sentence."}
                ],
                "stream": False,
            }
            response = await client.post(
                f"{base_url}/api/chat",
                json=payload,
            )
            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "")
                print(f"   ✅ Response: {content[:100]}...")
                return True
            else:
                print(f"   ❌ Error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def test_vision_model(
    base_url: str = "http://192.168.0.106:11434",
    model: str = "qwen2.5vl:7b"
) -> bool:
    """Test vision model with a simple image."""
    print(f"\n🖼️  Testing vision model: {model}...")
    
    # Create a simple 10x10 red PNG image (smallest valid PNG)
    # This is a 1x1 red pixel PNG
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x18, 0xDD,
        0x8D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,
        0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    base64_image = base64.b64encode(png_data).decode("utf-8")
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "What color is this image? Answer in one word.",
                        "images": [base64_image],
                    }
                ],
                "stream": False,
            }
            response = await client.post(
                f"{base_url}/api/chat",
                json=payload,
            )
            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "")
                print(f"   ✅ Response: {content[:100]}...")
                return True
            else:
                print(f"   ❌ Error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def test_ollama_client() -> bool:
    """Test the OllamaClient class."""
    print("\n🧪 Testing OllamaClient class...")
    
    try:
        from smart_file_manager.services.ollama_client import OllamaClient
        from smart_file_manager.services.model_config import ModelConfig, VISION_TIER, BALANCED_TIER
        
        config = ModelConfig(
            primary_tier=BALANCED_TIER,
            vision_tier=VISION_TIER,
        )
        
        async with OllamaClient(
            base_url="http://192.168.0.106:11434",
            fallback_url="http://192.168.0.107:11434",
            model_config=config,
        ) as client:
            # Test text completion
            print("   Testing text completion...")
            response = await client.chat_completion(
                messages=[{"role": "user", "content": "Say 'OllamaClient works!'"}],
                model="qwen2.5:7b",
            )
            print(f"   ✅ Text: {response.content[:50]}...")
            
            # Test vision
            print("   Testing vision analysis...")
            png_data = bytes([
                0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
                0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
                0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
                0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
                0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
                0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
                0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x18, 0xDD,
                0x8D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,
                0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
            ])
            base64_image = base64.b64encode(png_data).decode("utf-8")
            
            response = await client.vision_analysis(
                prompt="Describe this image briefly.",
                images=[base64_image],
            )
            print(f"   ✅ Vision: {response.content[:50]}...")
            
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Ollama Integration Test Suite")
    print("=" * 60)
    
    base_url = "http://192.168.0.106:11434"
    fallback_url = "http://192.168.0.107:11434"
    
    results = {}
    
    # Test connection
    results["connection"] = await test_ollama_connection(base_url)
    if not results["connection"]:
        print(f"\n⚠️  Trying fallback URL: {fallback_url}")
        results["connection"] = await test_ollama_connection(fallback_url)
        if results["connection"]:
            base_url = fallback_url
    
    if not results["connection"]:
        print("\n❌ Cannot connect to Ollama server. Exiting.")
        return 1
    
    # List models
    models = await test_list_models(base_url)
    
    # Test text model
    text_model = "qwen2.5:7b" if "qwen2.5:7b" in models else (models[0] if models else None)
    if text_model:
        results["text_model"] = await test_text_model(base_url, text_model)
    else:
        print("\n⚠️  No text model available to test")
        results["text_model"] = False
    
    # Test vision model
    vision_model = "qwen2.5vl:7b" if "qwen2.5vl:7b" in models else None
    if vision_model:
        results["vision_model"] = await test_vision_model(base_url, vision_model)
    else:
        print("\n⚠️  Vision model qwen2.5vl:7b not found. Please run: ollama pull qwen2.5vl:7b")
        results["vision_model"] = False
    
    # Test OllamaClient class
    results["ollama_client"] = await test_ollama_client()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
