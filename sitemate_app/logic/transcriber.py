import streamlit as st
from groq import Groq
import os

def transcribe_audio(audio_bytes):
    """
    Sends recorded audio to Groq's Distil-Whisper model for text transcription.
    """
    try:
        # 1. Initialize Groq Client
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        # 2. Save bytes to a temporary file (Groq API needs a file-like object)
        temp_filename = "temp_voice_input.wav"
        with open(temp_filename, "wb") as f:
            f.write(audio_bytes)
            
        # 3. Send to Groq Whisper
        with open(temp_filename, "rb") as file:
            transcription = client.audio.transcriptions.create(
              file=(temp_filename, file.read()),
              model="distil-whisper-large-v3-en", # Super fast model
              response_format="json",
              language="en",
              temperature=0.0
            )
        
        # 4. Cleanup
        os.remove(temp_filename)
        
        return transcription.text
        
    except Exception as e:
        return f"Error Transcribing: {e}"