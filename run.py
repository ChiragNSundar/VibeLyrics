"""
VibeLyrics Entry Point
Run this file to start the application
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    print("\nVibeLyrics - Collaborative Hip-Hop Lyric Writing Assistant")
    print("=" * 55)
    print("Starting server at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
