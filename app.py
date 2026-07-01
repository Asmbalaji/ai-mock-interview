import os
import re
import json
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, send_file
)
from groq import Groq
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

# Used as a fallback question source if the LLM call in generate_questions() fails
QUESTION_BANK = {
    "Software Engineer": [
        "Tell me about yourself and your technical background.",
        "Explain the difference between a process and a thread.",
        "Describe a challenging bug you fixed and how you approached it.",
        "How would you design a URL shortening service?",
        "Where do you see yourself in 5 years?",
    ],
    "Data Analyst": [
        "Walk me through how you would clean a messy dataset.",
        "Explain the difference between INNER JOIN and LEFT JOIN.",
        "How do you decide which chart type to use for a dataset?",
        "Describe a time your analysis changed a business decision.",
        "What metrics would you track for an e-commerce app?",
    ],
    "Product Manager": [
        "Tell me about a product you launched and its impact.",
        "How do you prioritize features with limited engineering resources?",
        "Walk me through how you'd improve a product I use daily.",
        "How do you handle disagreement with engineering on scope?",
        "How do you measure product success post-launch?",
    ],
    "HR / General": [
        "Tell me about yourself.",
        "What is your greatest strength and weakness?",
        "Why do you want to work with us?",
        "Describe a conflict you resolved at work.",
        "Where do you see yourself in 5 years?",
    ],
}


def evaluate_answer(role: str, question: str, answer: str) -> dict:
    """Call the LLM and return a structured evaluation dict."""
    prompt = f"""You are an expert technical and behavioral interviewer.

Role: {role}
Question: {question}
Candidate Answer: {answer or "(No answer provided)"}

Evaluate the answer and respond with ONLY valid JSON (no markdown, no extra text)
in exactly this shape:
{{
  "score": <integer 0-10>,
  "strengths": ["point1", "point2"],
  "improvements": ["point1", "point2"],
  "better_answer": "a concise improved answer"
}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    raw = response.choices[0].message.content.strip()

    # Strip accidental code fences
    raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()

    try:
        data = json.loads(raw)
        data["score"] = int(data.get("score", 0))
    except (json.JSONDecodeError, ValueError):
        data = {
            "score": 0,
            "strengths": [],
            "improvements": ["Could not parse AI response."],
            "better_answer": raw,
        }
    return data


def generate_questions(role, difficulty, interview_type):
    prompt = f"""
You are an expert interviewer.

Generate exactly 5 interview questions.

Role: {role}
Difficulty: {difficulty}
Interview Type: {interview_type}

IMPORTANT:
- Return ONLY a JSON array.
- Do NOT use markdown.
- Do NOT explain anything.
- Do NOT number the questions.

Example:

[
"Tell me about yourself.",
"Explain OOP.",
"What is multithreading?",
"Describe a challenging project.",
"Where do you see yourself in 5 years?"
]
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()

    try:
        questions = json.loads(raw)
        if isinstance(questions, list) and len(questions) > 0:
            return questions
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: use the static question bank if it has this role, else a generic set
    return QUESTION_BANK.get(role, [
        "Tell me about yourself.",
        "Explain one project you worked on.",
        "What are your strengths?",
        "Describe a challenge you solved.",
        "Why should we hire you?"
    ])


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        role = request.form["role"]
        difficulty = request.form["difficulty"]
        interview_type = request.form["type"]

        session["role"] = role
        session["difficulty"] = difficulty
        session["type"] = interview_type
        session["questions"] = generate_questions(role, difficulty, interview_type)

        session["current_index"] = 0
        session["results"] = []

        return redirect("/interview")

    return render_template("index.html", roles=list(QUESTION_BANK.keys()))


@app.route("/report")
def report():
    results = session.get("results", [])
    if not results:
        return redirect(url_for("home"))

    avg_score = round(sum(r["score"] for r in results) / len(results), 1)
    return render_template(
        "report.html",
        results=results,
        avg_score=avg_score,
        role=session.get("role", ""),
        date=datetime.now().strftime("%d %b %Y, %I:%M %p"),
    )


@app.route("/interview", methods=["GET", "POST"])
def interview():

    if "questions" not in session:
        return redirect(url_for("home"))

    idx = session["current_index"]
    questions = session["questions"]

    if request.method == "POST":
        answer = request.form.get("answer", "").strip()

        question = questions[idx]

        evaluation = evaluate_answer(
            session["role"],
            question,
            answer
        )

        results = session["results"]

        results.append({
            "question": question,
            "answer": answer,
            **evaluation
        })

        session["results"] = results
        session["current_index"] = idx + 1

        if session["current_index"] >= len(questions):
            return redirect(url_for("report"))

        return redirect(url_for("interview"))

    return render_template(
        "interview.html",
        question=questions[idx],
        progress=idx + 1,
        total=len(questions),
        role=session["role"]
    )


@app.route("/report/pdf")
def report_pdf():
    results = session.get("results", [])
    if not results:
        return redirect(url_for("home"))

    avg_score = round(sum(r["score"] for r in results) / len(results), 1)
    role = session.get("role", "")

    path = os.path.join(os.getcwd(), "interview_report.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                             topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=20)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceBefore=14)
    body = styles["BodyText"]

    elements = [
        Paragraph("AI Mock Interview — Performance Report", title_style),
        Spacer(1, 6),
        Paragraph(f"Role: {role}", body),
        Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", body),
        Paragraph(f"Overall Score: {avg_score} / 10", body),
        Spacer(1, 12),
    ]

    for i, r in enumerate(results, start=1):
        elements.append(Paragraph(f"Q{i}. {r['question']}", h2))
        elements.append(Paragraph(f"<b>Answer:</b> {r['answer'] or '(No answer)'}", body))
        elements.append(Paragraph(f"<b>Score:</b> {r['score']} / 10", body))

        if r.get("strengths"):
            elements.append(Paragraph(
                "<b>Strengths:</b> " + "; ".join(r["strengths"]), body))
        if r.get("improvements"):
            elements.append(Paragraph(
                "<b>Improvements:</b> " + "; ".join(r["improvements"]), body))
        if r.get("better_answer"):
            elements.append(Paragraph(
                f"<b>Suggested Better Answer:</b> {r['better_answer']}", body))
        elements.append(Spacer(1, 10))

    doc.build(elements)
    return send_file(path, as_attachment=True, download_name="interview_report.pdf")


@app.route("/restart")
def restart():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)