import os
from dotenv import load_dotenv

load_dotenv()

_model = None


def generate_summary(text: str) -> str:
    """Generate a summary from text using Gemini."""
    global _model
    
    if _model is None:
        import google.generativeai as genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""Please provide a concise and clear summary of the following text. 
The summary should capture the main points and be suitable for study purposes.

Text:
{text}

Summary:"""
    
    response = _model.generate_content(prompt)
    return response.text.strip()
