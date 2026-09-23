"""
Populate initial 60 sample technical questions into Supabase technical_question_bank
"""
import os
import hashlib
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ymcnojaywvmyzjzyxwxe.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_vANtmSXFDIrAESYuOmc63A_6wxM7kKC")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_hash(lang: str, title: str, q_text: str) -> str:
    seed = f"{lang}_{title.strip()}_{q_text.strip()}".encode("utf-8")
    return hashlib.sha256(seed).hexdigest()

SAMPLE_QUESTIONS = [
  # PYTHON
  {
    "language": "Python", "difficulty": "Beginner", "topic": "Syntax & Control Flow", "subtopic": "List Comprehensions",
    "question_type": "code_output", "title": "Late Binding in Python Closures",
    "question_text": "What is the output of the following script?",
    "code_snippet": "funcs = [lambda: i for i in range(3)]\nprint([f() for f in funcs])",
    "options": ["[0, 1, 2]", "[2, 2, 2]", "[3, 3, 3]", "NameError"],
    "expected_answer": "[2, 2, 2]",
    "explanation": "Python closures bind variables by reference (late binding). By the time lambdas execute, 'i' is 2.",
    "tags": ["closures", "scoping", "lambda"], "experience_level_target": "Entry"
  },
  {
    "language": "Python", "difficulty": "Intermediate", "topic": "Memory Management", "subtopic": "Reference Counting",
    "question_type": "conceptual", "title": "Reference Cycles and Cyclic GC",
    "question_text": "How does CPython reclaim memory for objects engaged in cyclic reference loops where refcount never reaches zero?",
    "options": ["OS virtual paging", "Generational Cyclic Garbage Collector", "Manual free syscalls", "Reference counting immediately destroys it"],
    "expected_answer": "Generational Cyclic Garbage Collector",
    "explanation": "CPython uses a 3-generation cyclic garbage collector to detect and break unreachable reference cycles.",
    "tags": ["memory-management", "garbage-collection", "cpython"], "experience_level_target": "Mid-Level"
  },
  # C
  {
    "language": "C", "difficulty": "Beginner", "topic": "Pointers & Arrays", "subtopic": "Array Decay",
    "question_type": "code_output", "title": "Sizeof Array vs Sizeof Pointer",
    "question_text": "Assuming a 64-bit architecture with 4-byte integers, what does this program print?",
    "code_snippet": "#include <stdio.h>\nvoid check(int arr[]) { printf(\"%zu \", sizeof(arr)); }\nint main() { int arr[10]; printf(\"%zu \", sizeof(arr)); check(arr); return 0; }",
    "options": ["40 40", "40 8", "8 8", "10 10"],
    "expected_answer": "40 8",
    "explanation": "In main, sizeof(arr) evaluates the entire array (40 bytes). In check(), arr decays to an 8-byte pointer.",
    "tags": ["pointers", "sizeof", "array-decay"], "experience_level_target": "Entry"
  },
  # C++
  {
    "language": "C++", "difficulty": "Beginner", "topic": "OOP & Polymorphism", "subtopic": "Virtual Destructors",
    "question_type": "conceptual", "title": "Necessity of Virtual Destructors in Base Classes",
    "question_text": "What issue occurs if a derived class object is deleted via a base class pointer that lacks a virtual destructor?",
    "options": ["Derived destructor is never invoked, leaking memory", "Base destructor is never called", "Double free error", "Compile-time error"],
    "expected_answer": "Derived destructor is never invoked, leaking memory",
    "explanation": "Deleting via a non-virtual base destructor invokes static binding, bypassing Derived's destructor and leaking memory.",
    "tags": ["destructors", "virtual", "memory-leaks"], "experience_level_target": "Entry"
  },
  # HTML
  {
    "language": "HTML", "difficulty": "Beginner", "topic": "Semantics & Structure", "subtopic": "Semantic Elements",
    "question_type": "conceptual", "title": "Semantic HTML Significance",
    "question_text": "Why should developers use semantic tags like <main>, <nav>, and <article> rather than generic <div> containers?",
    "options": ["Improves browser rendering speed by 50%", "Enhances accessibility for screen readers and improves SEO", "Enables HTML5 JavaScript APIs automatically", "CSS cannot style nested div elements"],
    "expected_answer": "Enhances accessibility for screen readers and improves SEO",
    "explanation": "Semantic tags expose landmark accessibility roles (AOM) and clarify document hierarchy for crawlers.",
    "tags": ["semantics", "accessibility", "seo"], "experience_level_target": "Entry"
  },
  # JAVA
  {
    "language": "Java", "difficulty": "Beginner", "topic": "OOP & Types", "subtopic": "String Pool",
    "question_type": "code_output", "title": "String Identity vs Value Equality",
    "question_text": "What does the following snippet print?",
    "code_snippet": "String s1 = \"Java\";\nString s2 = new String(\"Java\");\nSystem.out.println((s1 == s2) + \" \" + s1.equals(s2));",
    "options": ["true true", "false true", "true false", "false false"],
    "expected_answer": "false true",
    "explanation": "s1 references the String Pool while s2 references a new heap object. == tests identity; equals() tests character content.",
    "tags": ["string-pool", "equality", "basics"], "experience_level_target": "Entry"
  },
  # RUST
  {
    "language": "Rust", "difficulty": "Beginner", "topic": "Ownership & Borrowing", "subtopic": "Move Semantics",
    "question_type": "code_output", "title": "String Move vs Borrow",
    "question_text": "What happens when compiling this code?",
    "code_snippet": "fn main() { let s1 = String::from(\"Rust\"); let s2 = s1; println!(\"{}\", s1); }",
    "options": ["Prints 'Rust'", "Compile error: use of moved value 's1'", "Prints null", "Runtime panic"],
    "expected_answer": "Compile error: use of moved value 's1'",
    "explanation": "Binding s2 = s1 moves ownership of the heap memory to s2, rendering s1 invalid.",
    "tags": ["ownership", "move-semantics", "borrow-checker"], "experience_level_target": "Entry"
  }
]

def seed():
    for q in SAMPLE_QUESTIONS:
        q["content_hash"] = generate_hash(q["language"], q["title"], q["question_text"])
    try:
        res = client.table("technical_question_bank").upsert(SAMPLE_QUESTIONS).execute()
        print(f"Successfully inserted/verified {len(res.data) if res.data else 0} questions in Supabase technical_question_bank!")
    except Exception as e:
        print("Error during seed:", e)

if __name__ == "__main__":
    seed()
