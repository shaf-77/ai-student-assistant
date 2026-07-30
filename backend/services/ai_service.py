"""
ai_service.py
-------------
Handles all communication with the Gemini API.
Kept separate from routes so we can reuse it later for
Summarize (Feature 3) and Quiz Generation (Feature 4) too.
"""

import google.generativeai as genai
from config import Config

# Configure the Gemini client once with our API key
genai.configure(api_key=Config.GEMINI_API_KEY)

# Using Gemini's fast, cheap model -- good enough for Q&A and works quickly
model = genai.GenerativeModel("gemini-3.6-flash")
print("Using model: gemini-3.6-flash")

def answer_question_from_context(question, context_chunks):
    """
    Asks Gemini to answer a question using ONLY the provided context chunks.

    context_chunks: list of strings (the relevant note excerpts found by FAISS)
    """
    if not context_chunks:
        # No relevant chunks were found at all -- don't even call the AI,
        # we already know the answer isn't in the notes.
        return "I couldn't find anything about this in your uploaded notes."

    # Combine chunks into one context block, clearly separated
    context_text = "\n\n---\n\n".join(context_chunks)

    prompt = f"""You are a study assistant. Answer the student's question using ONLY the context below, which comes from their own uploaded notes.

Rules:
- If the answer is fully or partially contained in the context, answer it clearly and concisely.
- If the context does NOT contain the answer, respond exactly with: "This isn't covered in your uploaded notes."
- Do NOT use any outside knowledge. Do NOT make anything up.
- Keep the answer focused and student-friendly.

Context from notes:
{context_text}

Question: {question}

Answer:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API error: {e}")
        raise
def summarize_note(content, summary_type):
    """
    Generates a summary of a note's full content using Gemini.

    summary_type: one of "short", "detailed", "bullet"
    We use different prompts for each style, because asking Gemini
    generically for "a summary" tends to produce inconsistent length/format.
    Being explicit in the prompt gives much more reliable, predictable output.
    """

    instructions = {
        "short": (
            "Write a short summary in 2-3 sentences. "
            "Capture only the most important idea(s). Keep it concise."
        ),
        "detailed": (
            "Write a detailed, well-structured summary in paragraph form. "
            "Cover all major points and important supporting details, "
            "but do not simply repeat the original text word-for-word."
        ),
        "bullet": (
            "Summarize the content as a clean bullet-point list. "
            "Each bullet should cover one key idea. Use '-' for bullets. "
            "Keep each bullet concise (one line where possible)."
        )
    }

    instruction = instructions.get(summary_type)
    if not instruction:
        raise ValueError(f"Unknown summary_type: {summary_type}")

    prompt = f"""You are a study assistant helping a student review their notes.

{instruction}

Notes:
{content}

Summary:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API error (summarize): {e}")
        raise
import json
import re


def generate_quiz(content, question_type, difficulty, num_questions=5):
    """
    Generates quiz questions from note content using Gemini,
    returned as structured JSON so the frontend can render
    an interactive quiz (not just plain text).

    question_type: "mcq", "short_answer", or "mixed"
    difficulty: "easy", "medium", "hard"
    """

    difficulty_guides = {
        "easy": "Simple recall questions testing basic facts and definitions directly stated in the notes.",
        "medium": "Questions requiring understanding of concepts and how ideas connect, not just memorization.",
        "hard": "Challenging questions requiring analysis, application, or connecting multiple ideas from the notes."
    }

    type_instructions = {
        "mcq": (
            'Generate ONLY multiple-choice questions. Each question must have exactly 4 options, '
            'with exactly one correct answer.'
        ),
        "short_answer": (
            'Generate ONLY short-answer questions. Each should be answerable in 1-2 sentences.'
        ),
        "mixed": (
            'Generate a mix of multiple-choice and short-answer questions (roughly half and half).'
        )
    }

    # We instruct Gemini to output STRICT JSON matching this exact schema.
    # This is the key trick for getting structured, parseable output from an LLM.
    prompt = f"""You are a quiz generator for a student assistant app. Based ONLY on the notes below, generate {num_questions} quiz questions.

Difficulty level: {difficulty} - {difficulty_guides.get(difficulty, "")}
Question type: {type_instructions.get(question_type, "")}

Notes:
{content}

Respond with ONLY valid JSON, no other text, no markdown code fences, matching this exact structure:
{{
  "questions": [
    {{
      "type": "mcq",
      "question": "question text here",
      "options": ["option A", "option B", "option C", "option D"],
      "correct_answer": "the exact text of the correct option",
      "explanation": "brief explanation of why this is correct"
    }},
    {{
      "type": "short_answer",
      "question": "question text here",
      "correct_answer": "expected answer",
      "explanation": "brief explanation"
    }}
  ]
}}

For "mcq" type questions, always include the "options" array with 4 choices.
For "short_answer" type questions, omit the "options" field entirely.
Respond with ONLY the JSON object, nothing else."""

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # Gemini sometimes wraps JSON in ```json ... ``` even when told not to.
        # This strips those markdown fences if present, so json.loads() doesn't fail.
        raw_text = re.sub(r"^```json\s*|^```\s*|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()

        quiz_data = json.loads(raw_text)
        return quiz_data["questions"]

    except json.JSONDecodeError as e:
        print(f"Failed to parse quiz JSON: {e}\nRaw response: {raw_text}")
        raise ValueError("AI returned an invalid quiz format. Please try again.")
    except Exception as e:
        print(f"Gemini API error (quiz): {e}")
        raise