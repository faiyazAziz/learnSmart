import os
import fitz  # PyMuPDF
import google.generativeai as genai
import json
from django.conf import settings

# Configure the Gemini API key from Django settings
# IMPORTANT: You'll need to add your key to learnsmart/settings.py
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except AttributeError:
    print("WARNING: GEMINI_API_KEY not found in settings. AI features will not work.")

def extract_text_from_pdf(pdf_file):
    """Opens a PDF file object and extracts all text content."""
    try:
        # PyMuPDF needs a file path or bytes, not a Django File object directly
        # Reading the content into memory
        pdf_bytes = pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = "".join(page.get_text() for page in doc)
        doc.close()
        return full_text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def _call_gemini_api(prompt):
    """A helper function to call the Gemini API and parse the JSON response."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        # Clean up the response to ensure it's valid JSON
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"ERROR calling Gemini API or parsing JSON: {e}")
        return None

def get_topics_from_text(text):
    """Generates a list of topics from the provided text using the LLM."""
    prompt = f"""
    You are an academic assistant. Your task is to identify the main topics from the following text.
    Provide the output as a single JSON object with one key: "topics". This key should contain a list of strings.
    Example format: {{"topics": ["Topic 1", "Topic 2: Sub-topic"]}}

    Text to analyze:
    ---
    {text}
    """
    data = _call_gemini_api(prompt)
    return data.get("topics", []) if data else []

def get_questions_for_topic(topic_title, full_text):
    """Generates quiz questions for a specific topic using the LLM."""
    prompt = f"""
    You are an expert quiz creator. Based ONLY on the provided text, generate 2 multiple-choice questions for the topic: "{topic_title}".

    Instructions:
    1. Each question must have 4 options (A, B, C, D).
    2. Indicate the correct answer.
    3. Provide a brief explanation for the correct answer.

    Format your output as a JSON array of objects. Each object must have these keys: "question_text", "options" (an object), "correct_answer" (a string like 'A'), and "explanation".

    Relevant text:
    ---
    {full_text}
    """
    return _call_gemini_api(prompt)