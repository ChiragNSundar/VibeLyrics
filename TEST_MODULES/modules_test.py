from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

LMSTUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"

SYSTEM_PROMPT = """
You are a professional songwriter and lyric improver.

Your task:
- Improve the lyrics
- Keep the original meaning
- Fix rhyme scheme
- Make it catchy
- Make it emotionally impactful
- DO NOT explain anything
- ONLY output the improved lyrics
"""

def improve_lyrics(lyrics):
    prompt = f"""
You are a professional songwriter.

Rewrite and improve the following lyrics.
Keep meaning but:
- add rhyme
- improve flow
- make it emotional
- make it catchy
Structure:
Verse 1
Verse 2
Chorus (repeatable hook)
Return ONLY the lyrics.

Lyrics:
{lyrics}
"""

    payload = {
        "model": "mistralai/mistral-7b-instruct-v0.3",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.9,
        "max_tokens": 400
    }

    headers = {
        "Authorization": "Bearer lm-studio",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "http://127.0.0.1:1234/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120
    )

    data = response.json()

    if "choices" not in data:
        print("LM STUDIO ERROR:", data)
        return "Model failed. Check LM Studio console."

    return data["choices"][0]["message"]["content"]

@app.route("/lyrics", methods=["POST"])
def lyrics():
    user_lyrics = request.json.get("lyrics")

    if not user_lyrics:
        return jsonify({"error": "No lyrics provided"}), 400

    improved = improve_lyrics(user_lyrics)

    return jsonify({
        "original": user_lyrics,
        "improved": improved
    })


if __name__ == "__main__":
    app.run(port=5000, debug=True)