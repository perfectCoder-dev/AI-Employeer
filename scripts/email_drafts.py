"""Generate and package exact email drafts for human approval."""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from config import GROQ_API_URL, GROQ_MODEL, PENDING_APPROVAL, VAULT_DIR
from handbook_knowledge import classify_university_email, retrieve_handbook_context
from workflow_utils import extract_email_address, unique_path, write_markdown_with_frontmatter


def categorize_email_by_content(content: str) -> str:
    return classify_university_email(content)


def _sender_first_name(original_from: str) -> str:
    name_match = re.search(r"^([A-Za-z\s]+)(?:\s*<|$)", original_from or "")
    return name_match.group(1).strip().split()[0] if name_match else "there"


def generate_contextual_reply(
    original_content: str,
    original_subject: str,
    original_from: str,
    handbook_context: str = "",
) -> str:
    sender_name = _sender_first_name(original_from)
    category = categorize_email_by_content(original_content)
    content_lower = original_content.lower()
    handbook_context = handbook_context or retrieve_handbook_context(
        f"{original_subject}\n{original_content}"
    )
    page_refs = ", ".join(re.findall(r"Handbook page (\d+)", handbook_context))

    is_formal = any(
        term in content_lower
        for term in ["dear", "regards", "sincerely", "respectfully", "good morning", "good afternoon"]
    )
    is_casual = any(term in content_lower for term in ["hi", "hey", "thanks", "awesome", "cool", "sounds good"])
    greeting = f"Hi {sender_name}," if is_casual or not is_formal else f"Dear {sender_name},"
    signoff = "Best,\nAI Employee Assistant" if is_casual or not is_formal else "Best regards,\nAI Employee Assistant"

    if handbook_context:
        context_text = re.sub(r"^\[Handbook page \d+\]\s*", "", handbook_context.splitlines()[0])
        first_sentence = re.split(r"(?<=[.!?])\s+", context_text.strip())[0]
        if len(first_sentence) > 220:
            first_sentence = first_sentence[:217].rstrip() + "..."
        reference_text = f" (Handbook page {page_refs.split(', ')[0]})" if page_refs else ""
        middle = (
            f"Thank you for contacting the department about \"{original_subject}\". "
            f"According to the undergraduate handbook{reference_text}, {first_sentence} "
            "Please review the relevant handbook section and contact the department office if your case needs verification or a formal request."
        )
    else:
        middle = (
            f"Thank you for contacting the department about \"{original_subject}\". "
            "I do not have enough handbook context to give a policy-specific answer from the available material. "
            "Please share your program, semester, roll number, and the specific issue so the department can guide you correctly."
        )

    return f"{greeting}\n\n{middle}\n\n{signoff}"


def generate_email_reply(
    original_content: str,
    original_subject: str,
    original_from: str,
    handbook_context: str = "",
) -> str:
    retrieved_context = retrieve_handbook_context(f"{original_subject}\n{original_content}")
    effective_context = retrieved_context or handbook_context
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            import requests

            response = requests.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a university department email assistant. "
                                "Write a helpful, specific, professional reply to a student, parent, faculty member, or staff member. "
                                "Use only the handbook context provided. If the answer is not present, say the department will need to verify it. "
                                "Keep it under 180 words. Do not invent deadlines, approvals, exceptions, fees, or eligibility. "
                                "Mention relevant handbook page references when present. "
                                "Sign off as 'Department Office'.\n\n"
                                f"Relevant handbook context:\n{effective_context[:2800]}"
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Subject: {original_subject}\n"
                                f"From: {original_from}\n\n"
                                f"{original_content}"
                            ),
                        },
                    ],
                    "temperature": 0.5,
                    "max_tokens": 300,
                },
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    return generate_contextual_reply(original_content, original_subject, original_from, effective_context)


def create_email_approval_artifact(
    source_file: Path,
    original_frontmatter: dict,
    original_body: str,
    draft_body: str,
    pending_dir: Path = PENDING_APPROVAL,
) -> Path:
    original_subject = original_frontmatter.get("subject", "No Subject")
    to_address = original_frontmatter.get("to") or extract_email_address(original_frontmatter.get("from", ""))
    subject = original_subject if str(original_subject).startswith("Re:") else f"Re: {original_subject}"
    action_id = f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{source_file.stem}"
    filename = f"APPROVE_{source_file.stem}.md"
    approval_path = unique_path(pending_dir, filename)
    handbook_context = retrieve_handbook_context(f"{original_subject}\n{original_body}")
    handbook_pages = sorted(set(re.findall(r"Handbook page (\d+)", handbook_context)), key=int)

    body = f"""# Email Approval

## Draft Reply

{draft_body}

## Handbook Context

{handbook_context or "No matching handbook section was found automatically."}

## Original Email

{original_body}
"""
    frontmatter = {
        "type": "email_send",
        "status": "pending_approval",
        "action_id": action_id,
        "source_file": source_file.name,
        "to": to_address,
        "subject": subject,
        "created": datetime.now().isoformat(),
        "draft_body": draft_body,
        "original_email_id": original_frontmatter.get("original_email_id"),
        "university_category": classify_university_email(f"{original_subject}\n{original_body}"),
        "handbook_pages": handbook_pages,
    }
    return write_markdown_with_frontmatter(approval_path, frontmatter, body)


def read_company_handbook() -> str:
    candidates = [
        VAULT_DIR / "docs" / "University_Handbook.md",
        VAULT_DIR / "docs" / "Company_Handbook.md",
        VAULT_DIR / "Company_Handbook.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    return ""
