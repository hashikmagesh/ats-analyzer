# test_api_connection.py
# Run: python test_api_connection.py

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=" * 50)
print("     API CONNECTION TEST")
print("=" * 50)

# ── Test Gemini ───────────────────────────────────────
print("\n📡 Testing Gemini...")
try:
    import requests

    gemini_key = os.getenv('GEMINI_API_KEY', '')

    if not gemini_key:
        print("  ❌ GEMINI_API_KEY not found in .env")
    else:
        url     = (
            f"https://generativelanguage.googleapis.com"
            f"/v1beta/models/gemini-2.5-flash"
            f":generateContent?key={gemini_key}"
        )
        headers = {"Content-Type": "application/json"}
        data    = {
            "contents": [{
                "parts": [{"text": "Say exactly: GEMINI_WORKS"}]
            }]
        }

        response = requests.post(
            url, headers=headers, json=data, timeout=15
        )

        if response.status_code == 200:
            result = response.json()
            reply  = result["candidates"][0]["content"]["parts"][0]["text"]
            print(f"  ✅ Gemini connected!")
            print(f"  Model : gemini-2.5-flash")
            print(f"  Reply : {reply.strip()}")
        else:
            print(f"  ❌ Gemini failed: {response.status_code}")
            print(f"  Error : {response.text[:300]}")

except Exception as e:
    print(f"  ❌ Gemini failed: {e}")


# ── Test OpenAI ───────────────────────────────────────
print("\n📡 Testing OpenAI...")
try:
    from openai import OpenAI
    openai_key = os.getenv('OPENAI_API_KEY', '')

    if not openai_key:
        print("  ❌ OPENAI_API_KEY not found in .env")
    else:
        client   = OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{
                'role':    'user',
                'content': 'Say exactly: OPENAI_WORKS'
            }],
            max_tokens=10,
        )
        reply = response.choices[0].message.content.strip()
        if 'OPENAI' in reply.upper():
            print(f"  ✅ OpenAI connected!")
            print(f"  Response: {reply}")
        else:
            print(f"  ⚠️  OpenAI replied but unexpected: {reply}")

except Exception as e:
    print(f"  ❌ OpenAI failed: {e}")


# ── Test AI Suggester (Step 11) ───────────────────────
print("\n📡 Testing AI Suggester...")
try:
    from analyzer.services.ai_suggester import (
        OPENAI_AVAILABLE, GEMINI_AVAILABLE
    )
    print(f"  OpenAI available: {OPENAI_AVAILABLE}")
    print(f"  Gemini available: {GEMINI_AVAILABLE}")

    if OPENAI_AVAILABLE or GEMINI_AVAILABLE:
        print("  ✅ At least one AI provider ready")
    else:
        print("  ❌ No AI provider detected — "
              "check your .env keys")

except Exception as e:
    print(f"  ❌ AI Suggester import failed: {e}")


# ── Test AI Rewriter (Step 12) ────────────────────────
print("\n📡 Testing AI Rewriter...")
try:
    from analyzer.services.resume_rewriter import (
        OPENAI_AVAILABLE, GEMINI_AVAILABLE
    )
    print(f"  OpenAI available: {OPENAI_AVAILABLE}")
    print(f"  Gemini available: {GEMINI_AVAILABLE}")

    if OPENAI_AVAILABLE or GEMINI_AVAILABLE:
        print("  ✅ Rewriter AI provider ready")
    else:
        print("  ❌ Rewriter will use rule-based fallback")

except Exception as e:
    print(f"  ❌ Rewriter import failed: {e}")


print("\n" + "=" * 50)
print("     SUMMARY")
print("=" * 50)