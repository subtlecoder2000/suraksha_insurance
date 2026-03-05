"""
config/languages.py
Supported languages and their locale codes for PROJECT RenewAI v2.0
"""

LANGUAGES = {
    "Hindi":     {"code": "hi-IN", "tts": "hi-IN-SwaraNeural",   "script": "Devanagari"},
    "English":   {"code": "en-IN", "tts": "en-IN-NeerjaNeural",  "script": "Latin"},
    "Tamil":     {"code": "ta-IN", "tts": "ta-IN-PallaviNeural", "script": "Tamil"},
    "Telugu":    {"code": "te-IN", "tts": "te-IN-ShrutiNeural",  "script": "Telugu"},
    "Bengali":   {"code": "bn-IN", "tts": "bn-IN-TanishaaNeural","script": "Bengali"},
    "Marathi":   {"code": "mr-IN", "tts": "mr-IN-AarohiNeural",  "script": "Devanagari"},
    "Kannada":   {"code": "kn-IN", "tts": "kn-IN-SapnaNeural",   "script": "Kannada"},
    "Malayalam": {"code": "ml-IN", "tts": "ml-IN-SobhanaNeural", "script": "Malayalam"},
    "Gujarati":  {"code": "gu-IN", "tts": "gu-IN-DhwaniNeural",  "script": "Gujarati"},
}

LANGUAGE_CODES = list(LANGUAGES.keys())

GREETING = {
    "Hindi":     "नमस्ते",
    "English":   "Hello",
    "Tamil":     "வணக்கம்",
    "Telugu":    "నమస్కారం",
    "Bengali":   "নমস্কার",
    "Marathi":   "नमस्कार",
    "Kannada":   "ನಮಸ್ಕಾರ",
    "Malayalam": "നമസ്കാരം",
    "Gujarati":  "નમસ્તે",
}
