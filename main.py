#This is a python File

#from google import genai

#client = genai.Client(api_key="AIzaSyC3XOsYy-Tqw25cAK_opEZ0435vZQnvKl0")

#response = client.models.generate_content(
#    model="gemini-2.5-flash",
#    contents="Explain how AI works in a few words",
#)

#print(response.text)

import os
import json
import google.generativeai as genai
from tkinter import *
from tkinter import filedialog, messagebox
from fpdf import FPDF
import PyPDF2
from docx import Document

genai.configure(api_key="AIzaSyC3XOsYy-Tqw25cAK_opEZ0435vZQnvKl0")

GENERATED_FOLDER = "generated"
os.makedirs(GENERATED_FOLDER, exist_ok=True)


def create_pdf(quiz_list, file_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", size=12)

    for i, q in enumerate(quiz_list, start=1):
        pdf.multi_cell(0, 8, f"Q{i}: {q['question']}")
        for choice in q["options"]:
            pdf.multi_cell(0, 8, f"    - {choice}")
        pdf.multi_cell(0, 8, f"Answer: {q['correct_answer']}")
        pdf.ln(5)

    pdf.output(file_path)


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        raise Exception(f"Error reading PDF: {e}")
    return text


def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        raise Exception(f"Error reading DOCX: {e}")
    return text


def pick_file():
    file_path = filedialog.askopenfilename(
        title="Select study file",
        filetypes=[
            ("PDF files", "*.pdf"),
            ("Word documents", "*.docx"),
            ("All files", "*.*")
        ]
    )
    if not file_path:
        return

    file_label.config(text=f"Selected: {os.path.basename(file_path)}")
    process_file(file_path)


def process_file(path):
    try:
        # Extract text based on file type
        file_ext = os.path.splitext(path)[1].lower()
        
        if file_ext == '.pdf':
            text_content = extract_text_from_pdf(path)
        elif file_ext == '.docx':
            text_content = extract_text_from_docx(path)
        else:
            # For other file types, try reading as plain text
            with open(path, 'r', encoding='utf-8') as f:
                text_content = f.read()

        if not text_content.strip():
            messagebox.showerror("Error", "No text could be extracted from the file.")
            return

        # Update UI to show processing
        output_text.delete(1.0, END)
        output_text.insert(END, "Processing file with Gemini AI...\n\n")
        root.update()

        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
        You are reading study material. Based on the content below, generate practice questions and study materials.

        Produce ONLY valid JSON with this exact structure:
        {{
            "questions": [
                {{
                    "question": "question text here",
                    "options": ["option A", "option B", "option C", "option D"],
                    "correct_answer": "the correct option text"
                }}
            ],
            "quizlet": [
                {{
                    "term": "key term",
                    "definition": "definition of the term"
                }}
            ]
        }}

        Generate at least 10 multiple choice questions and 15 flashcard terms.
        The questions and terms MUST be based ONLY on the material provided below.

        STUDY MATERIAL:
        {text_content}
        """

        response = model.generate_content(prompt)
        result_text = response.text
        
        # Clean up response if it contains markdown code blocks
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        data = json.loads(result_text)

        # Validate data structure
        if "questions" not in data or "quizlet" not in data:
            raise ValueError("Invalid response format from AI")

        # Save Quizlet text file (tab-separated format)
        quizlet_path = os.path.join(GENERATED_FOLDER, "quizlet.txt")
        with open(quizlet_path, "w", encoding='utf-8') as f:
            for item in data["quizlet"]:
                # Quizlet uses tab-separated format: term\tdefinition
                f.write(f"{item['term']}\t{item['definition']}\n")

        # Create PDF
        pdf_path = os.path.join(GENERATED_FOLDER, "quiz.pdf")
        create_pdf(data["questions"], pdf_path)

        # Update UI
        output_text.delete(1.0, END)
        output_text.insert(END, "✓ Quiz Generated Successfully!\n\n")
        output_text.insert(END, f"Generated {len(data['questions'])} questions and {len(data['quizlet'])} flashcards\n\n")
        output_text.insert(END, "--- Sample Questions ---\n")
        
        # Show first 5 questions as preview
        for i, q in enumerate(data["questions"][:5], start=1):
            output_text.insert(END, f"\nQ{i}: {q['question']}\n")
            for opt in q["options"]:
                output_text.insert(END, f"  • {opt}\n")
            output_text.insert(END, f"✓ Answer: {q['correct_answer']}\n")

        if len(data["questions"]) > 5:
            output_text.insert(END, f"\n... and {len(data['questions']) - 5} more questions in the PDF\n")

        messagebox.showinfo(
            "Success",
            f"Files generated successfully!\n\n"
            f"📄 Quiz PDF: {pdf_path}\n"
            f"📝 Flashcards TXT: {quizlet_path}\n\n"
            f"Total: {len(data['questions'])} questions, {len(data['quizlet'])} flashcards\n\n"
            f"Import the TXT file directly into Quizlet!"
        )

    except json.JSONDecodeError as e:
        messagebox.showerror("Error", f"Failed to parse AI response:\n{e}\n\nThe AI may have returned invalid JSON.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process file:\n{e}")
        output_text.delete(1.0, END)
        output_text.insert(END, f"Error: {e}")


# --- GUI SETUP ---
root = Tk()
root.title("AI Quiz Generator (Gemini)")
root.geometry("750x650")

title_label = Label(root, text="AI Quiz Generator", font=("Arial", 20, "bold"))
title_label.pack(pady=15)

instruction_label = Label(
    root, 
    text="Upload a PDF or DOCX file to generate practice questions and flashcards",
    font=("Arial", 10),
    fg="gray"
)
instruction_label.pack()

file_button = Button(
    root, 
    text="📁 Upload Study File", 
    command=pick_file,
    font=("Arial", 12),
    bg="#4CAF50",
    fg="white",
    padx=20,
    pady=10
)
file_button.pack(pady=10)

file_label = Label(root, text="No file selected", fg="gray", font=("Arial", 9))
file_label.pack(pady=5)

output_frame = Frame(root)
output_frame.pack(pady=10, padx=20, fill=BOTH, expand=True)

scrollbar = Scrollbar(output_frame)
scrollbar.pack(side=RIGHT, fill=Y)

output_text = Text(
    output_frame, 
    width=80, 
    height=25,
    yscrollcommand=scrollbar.set,
    font=("Consolas", 10)
)
output_text.pack(side=LEFT, fill=BOTH, expand=True)
scrollbar.config(command=output_text.yview)

footer_label = Label(
    root,
    text="Generated files will be saved in the 'generated' folder",
    font=("Arial", 8),
    fg="gray"
)
footer_label.pack(pady=5)

root.mainloop()