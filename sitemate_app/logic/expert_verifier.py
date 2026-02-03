from groq import Groq
import streamlit as st
import pandas as pd

def verify_project_budget(boq_df, location):
    """
    Sends the BOQ to Groq AI (Llama 3.3) for a 'Senior QS' Audit.
    Checks for: Under-estimation, Missing items, Price spikes.
    """
    try:
        # 1. Get Groq Key
        api_key = st.secrets.get("GROQ_API_KEY")
        if not api_key:
            return "❌ Error: GROQ_API_KEY not found in secrets."
            
        # 2. Configure Client
        client = Groq(api_key=api_key)
        
        # 3. Convert BOQ to string for AI analysis
        boq_summary = boq_df.to_string(index=False)
        
        prompt = f"""
        Act as a Senior Registered Quantity Surveyor (NIQS/RICS Certified). 
        Review this Construction Bill of Quantities for a project in {location}.
        
        BOQ DATA:
        {boq_summary}
        
        PERFORM A STRICT AUDIT:
        1. REALISM CHECK: Are these prices realistic for the current Nigerian market?
        2. MISSING ITEMS: What obvious items are missing? (e.g., if blocks exist, is there mortar?)
        3. RISK SCORE: Rate the budget confidence (0-100%).
        4. VERDICT: "VERIFIED" or "FLAGGED FOR REVIEW".
        
        Format output nicely with bold headers and bullet points. 
        Keep it professional and concise.
        """
        
        # 4. Generate Content
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            # UPDATED MODEL: Switched to the latest supported version
            model="llama-3.3-70b-versatile", 
            temperature=0.3, 
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        return f"❌ Verification Failed: {str(e)}"