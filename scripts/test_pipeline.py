#!/usr/bin/env python3
"""
Focused workflow tests for the Personal AI Employee system.

These tests avoid live Gmail, LinkedIn, and Groq calls. They validate the local
artifact contract that keeps production actions human-approved and repeatable.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from email_drafts import create_email_approval_artifact, generate_contextual_reply
from handbook_knowledge import classify_university_email, retrieve_handbook_context
from workflow_utils import read_markdown_with_frontmatter, write_markdown_with_frontmatter


def test_handbook_retrieval_finds_attendance_policy():
    context = retrieve_handbook_context("Can I sit in final exam with less than 75% attendance?")
    assert "Handbook page" in context
    assert "75%" in context or "attendance" in context.lower()


def test_university_email_classifier():
    assert classify_university_email("How can I freeze my semester?") == "semester_freeze"
    assert classify_university_email("What is the refund policy for fees?") == "fees_refund"


def test_email_approval_artifact_contains_exact_draft():
    with TemporaryDirectory() as tmp:
        source = Path(tmp) / "email_123_Project.md"
        source.write_text("original", encoding="utf-8")

        draft = "Hi Alex,\n\nThanks for reaching out.\n\nBest,\nAI Employee Assistant"
        approval = create_email_approval_artifact(
            source_file=source,
            original_frontmatter={
                "from": "Alex Client <alex@example.com>",
                "subject": "Project",
                "original_email_id": "gmail-123",
            },
            original_body="**Email Content:**\n\nCan you send pricing?",
            draft_body=draft,
            pending_dir=Path(tmp) / "Pending_Approval",
        )

        frontmatter, body = read_markdown_with_frontmatter(approval)
        assert frontmatter["type"] == "email_send"
        assert frontmatter["to"] == "alex@example.com"
        assert frontmatter["subject"] == "Re: Project"
        assert frontmatter["draft_body"] == draft
        assert frontmatter["university_category"] in {"course_registration", "fees_refund", "general_inquiry"}
        assert "## Draft Reply" in body
        assert "## Handbook Context" in body
        assert draft in body


def test_contextual_reply_fallback_is_deterministic():
    reply = generate_contextual_reply(
        original_content="Hi, can we schedule a call next week?",
        original_subject="Intro Call",
        original_from="Sam <sam@example.com>",
    )

    assert reply.startswith("Hi Sam,")
    assert "Intro Call" in reply
    assert "AI Employee Assistant" in reply


def test_approval_watcher_sends_only_approved_draft():
    import approval_watcher as approval_module

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        approved = root / "Approved"
        done = root / "Done"
        failed = root / "Failed"
        logs = root / "Logs"
        approved.mkdir()

        file_path = approved / "APPROVE_email.md"
        expected_body = "Approved body only."
        write_markdown_with_frontmatter(
            file_path,
            {
                "type": "email_send",
                "action_id": "email-test-1",
                "to": "client@example.com",
                "subject": "Re: Hello",
                "draft_body": expected_body,
            },
            "# Email Approval\n\n## Draft Reply\n\nApproved body only.",
        )

        watcher = approval_module.ApprovalWatcher(approved, done, failed)
        watcher.receipts_path = logs / "execution_receipts.json"
        watcher.executed_action_ids = set()

        sent = {}
        watcher.send_gmail = lambda to, subject, body: sent.update(
            {"to": to, "subject": subject, "body": body}
        ) or True
        approval_module.append_log = lambda *args, **kwargs: None

        watcher.process_file(file_path)

        assert sent == {
            "to": "client@example.com",
            "subject": "Re: Hello",
            "body": expected_body,
        }
        assert (done / "APPROVE_email.md").exists()
        assert not file_path.exists()


def test_approval_watcher_rejects_email_without_draft_body():
    import approval_watcher as approval_module

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        approved = root / "Approved"
        done = root / "Done"
        failed = root / "Failed"
        approved.mkdir()

        file_path = approved / "unsafe_email.md"
        write_markdown_with_frontmatter(
            file_path,
            {
                "type": "email_send",
                "action_id": "email-test-2",
                "to": "client@example.com",
                "subject": "Re: Hello",
            },
            "Old-style approval file without exact approved body.",
        )

        watcher = approval_module.ApprovalWatcher(approved, done, failed)
        watcher.send_gmail = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("send_gmail should not be called")
        )
        approval_module.append_log = lambda *args, **kwargs: None

        watcher.process_file(file_path)

        assert (failed / "unsafe_email.md").exists()


def test_dashboard_rejects_unsafe_filenames():
    import sys

    dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"
    sys.path.insert(0, str(dashboard_dir))
    try:
        import app as dashboard_app
    except ModuleNotFoundError as exc:
        if exc.name == "flask":
            print("SKIP dashboard filename validation; Flask is not installed in this environment")
            return
        raise

    assert dashboard_app.safe_filename("APPROVE_email.md") == "APPROVE_email.md"
    assert dashboard_app.safe_filename("../APPROVE_email.md") is None
    assert dashboard_app.safe_filename(".hidden.md") is None
    assert dashboard_app.safe_filename("notes.txt") is None


def test_dashboard_requires_token_when_configured():
    import sys

    dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"
    sys.path.insert(0, str(dashboard_dir))
    try:
        import app as dashboard_app
    except ModuleNotFoundError as exc:
        if exc.name == "flask":
            print("SKIP dashboard token validation; Flask is not installed in this environment")
            return
        raise

    original_token = dashboard_app.DASHBOARD_APPROVAL_TOKEN
    dashboard_app.DASHBOARD_APPROVAL_TOKEN = "test-token"
    try:
        client = dashboard_app.app.test_client()
        denied = client.get("/api/stats")
        assert denied.status_code == 403

        allowed = client.get("/api/stats", headers={"X-Approval-Token": "test-token"})
        assert allowed.status_code == 200
    finally:
        dashboard_app.DASHBOARD_APPROVAL_TOKEN = original_token


def test_gmail_note_filename_includes_message_id_and_is_unique():
    import gmail_watcher as gmail_module

    with TemporaryDirectory() as tmp:
        watcher = object.__new__(gmail_module.GmailWatcher)
        watcher.needs_action_path = Path(tmp)

        email_data = {
            "id": "gmail-message-123",
            "from": "Student <student@example.com>",
            "subject": "Attendance Question",
            "received": "2026-06-18T10:00:00",
            "labels": [],
            "body": "Can I sit the final with 74% attendance?",
            "snippet": "",
        }

        first = gmail_module.GmailWatcher.create_note_from_email(watcher, email_data)
        second = gmail_module.GmailWatcher.create_note_from_email(watcher, email_data)

        assert first.exists()
        assert second.exists()
        assert first != second
        assert "gmail-message-123" in first.name
        assert "gmail-message-123" in second.name


if __name__ == "__main__":
    print("Running AI Employee workflow tests...\n")
    test_handbook_retrieval_finds_attendance_policy()
    print("OK handbook retrieval")
    test_university_email_classifier()
    print("OK university classifier")
    test_email_approval_artifact_contains_exact_draft()
    print("OK approval artifact")
    test_contextual_reply_fallback_is_deterministic()
    print("OK fallback draft")
    test_approval_watcher_sends_only_approved_draft()
    print("OK exact approved email send")
    test_approval_watcher_rejects_email_without_draft_body()
    print("OK fail-closed email approval")
    test_dashboard_rejects_unsafe_filenames()
    print("OK dashboard filename validation")
    test_dashboard_requires_token_when_configured()
    print("OK dashboard token validation")
    test_gmail_note_filename_includes_message_id_and_is_unique()
    print("OK Gmail note filename uniqueness")
    print("\nAll workflow tests passed.")
