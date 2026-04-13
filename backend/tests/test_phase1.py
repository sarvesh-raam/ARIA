"""
ARIA Phase 1 — Quick Test Script
Run this AFTER starting the server to verify everything works.

Usage:
  1. Start server: python main.py
  2. In a new terminal: python test_phase1.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("\n[?] Testing health check...")
    r = requests.get(f"{BASE_URL}/")
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")
    assert r.status_code == 200, "Health check failed!"
    print("   ✅ Server is running!")

def test_upload(pdf_path: str):
    print(f"\n📄 Uploading document: {pdf_path}")
    with open(pdf_path, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/api/upload",
            files={"file": (pdf_path, f, "application/pdf")}
        )
    data = r.json()
    print(f"   Status: {r.status_code}")
    print(f"   Doc ID: {data.get('doc_id')}")
    print(f"   Company: {data.get('company')}")
    print(f"   Chunks: {data.get('chunks')}")
    print(f"   ✅ Upload successful!")
    return data.get("doc_id")

def test_query(doc_id: str, question: str):
    print(f"\n❓ Question: {question}")
    r = requests.post(
        f"{BASE_URL}/api/query",
        json={"doc_id": doc_id, "question": question}
    )
    data = r.json()
    print(f"   Answer: {data.get('answer')}")
    print(f"   ✅ Query successful!")

def test_list():
    print("\n📋 Listing all documents...")
    r = requests.get(f"{BASE_URL}/api/documents")
    docs = r.json()
    print(f"   Found {len(docs)} document(s)")
    for doc in docs:
        print(f"   - {doc['filename']} (ID: {doc['doc_id']})")
    print("   ✅ List successful!")

if __name__ == "__main__":
    print("=" * 50)
    print(" ARIA Phase 1 — Test Suite")
    print("=" * 50)

    # Step 1: Health check
    test_health()

    # Step 2: Upload a PDF (change path to any PDF you have)
    PDF_PATH = "test_document.pdf"  # Put any PDF here
    import os
    if not os.path.exists(PDF_PATH):
        print(f"\n⚠️  No test PDF found at '{PDF_PATH}'")
        print("   Download any company annual report PDF and name it 'test_document.pdf'")
        print("   Then run this script again.")
        exit(0)

    doc_id = test_upload(PDF_PATH)

    # Step 3: Ask questions
    questions = [
        "What is the company's total revenue?",
        "Who are the key executives mentioned?",
        "What are the main risks mentioned in the document?",
        "What is the net profit or loss?",
    ]

    for q in questions:
        test_query(doc_id, q)

    # Step 4: List all documents
    test_list()

    print("\n" + "=" * 50)
    print(" 🎉 All tests passed! Phase 1 is working!")
    print("=" * 50)
