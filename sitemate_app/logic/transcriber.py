import streamlit as st
from groq import Groq
import os

def transcribe_audio(audio_bytes):
    """
    Sends recorded audio to Groq's Whisper model for text transcription.
    Updated to use the stable 'whisper-large-v3' model.
    """
    try:
        # 1. Initialize Groq Client
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        # 2. Save bytes to a temporary file
        temp_filename = "temp_voice_input.wav"
        with open(temp_filename, "wb") as f:
            f.write(audio_bytes)
            
        # 3. Send to Groq Whisper (UPDATED MODEL)
        with open(temp_filename, "rb") as file:
            transcription = client.audio.transcriptions.create(
              file=(temp_filename, file.read()),
              model="whisper-large-v3", # <--- FIXED MODEL NAME
              response_format="json",
              language="en",
              temperature=0.0
            )
        
        # 4. Cleanup
        os.remove(temp_filename)
        
        return transcription.text
        
    except Exception as e:
        return f"Error: {e}"