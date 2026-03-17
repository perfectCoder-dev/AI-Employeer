import os
import time
import yaml
import json
import shutil
from pathlib import Path
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv(Path("/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/scripts/scripts/.env"))
except ImportError:
    pass

VAULT_DIR = Path("/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault").resolve()

def read_markdown_with_frontmatter(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1].strip())
                return frontmatter, parts[2].strip()
            except yaml.YAMLError as e:
                print(f"Error parsing YAML: {e}")
                return None, content
    return {}, content

def post_to_linkedin_browser(post_text):
    try:
        from playwright.sync_api import sync_playwright
        email = os.getenv('LINKEDIN_EMAIL')
        password = os.getenv('LINKEDIN_PASSWORD')
        if not email or not password:
            raise ValueError("LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env")
        print("Launching browser for LinkedIn posting...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=500)
            page = browser.new_page()
            page.set_default_timeout(60000)
            page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(2000)
            page.fill('#username', email)
            page.fill('#password', password)
            page.click('[type="submit"]')
            page.wait_for_timeout(5000)
            print("Logged into LinkedIn...")

            # Wait for feed
            page.wait_for_timeout(3000)

            # Go to LinkedIn feed
            page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(3000)

            # Click Start a post box at top of feed
            post_box_selectors = [
                'text=Start a post',
                '[placeholder="Start a post"]',
                'button:has-text("Start a post")',
                '.share-box-feed-entry__trigger',
                'button.share-box-feed-entry__trigger'
            ]
            clicked = False
            for selector in post_box_selectors:
                try:
                    page.click(selector, timeout=5000)
                    clicked = True
                    print(f"Clicked post box: {selector}")
                    break
                except:
                    continue

            if not clicked:
                page.screenshot(path="/tmp/linkedin_feed2.png")
                raise Exception("Could not click Start a post")

            page.wait_for_timeout(2000)

            # Try to find the editor
            editor_selectors = [
                '.ql-editor',
                '[data-placeholder]',
                '[contenteditable="true"]',
                'div[role="textbox"]'
            ]
            typed = False
            for selector in editor_selectors:
                try:
                    page.click(selector, timeout=5000)
                    page.keyboard.type(post_text)
                    typed = True
                    print(f"Typed content using selector: {selector}")
                    break
                except:
                    continue

            if not typed:
                # Take screenshot for debugging
                page.screenshot(path='/tmp/linkedin_debug.png')
                raise Exception("Could not find text editor - screenshot saved to /tmp/linkedin_debug.png")

            page.wait_for_timeout(1000)

            # Click Post button
            submit_selectors = [
                'button.share-actions__primary-action',
                'button:has-text("Post")',
                'button:has-text("Done")',
                '[data-control-name="share.post"]'
            ]
            for selector in submit_selectors:
                try:
                    page.click(selector, timeout=5000)
                    print("Clicked Post button")
                    break
                except:
                    continue

            page.wait_for_timeout(3000)
            print("Post published on LinkedIn!")
            browser.close()
            return {"id": f"linkedin_{datetime.now().strftime('%Y%m%d_%H%M%S')}", "status": "posted"}
    except ImportError:
        print("Playwright not installed. Falling back to queue.")
        return None
    except Exception as e:
        print(f"Browser automation failed: {e}. Falling back to queue.")
        return None

def post_to_linkedin(post_text):
    result = post_to_linkedin_browser(post_text)
    if result:
        return result
    print("Using queue fallback...")
    queue_entry = {"timestamp": datetime.now().isoformat(), "content": post_text, "status": "queued_for_manual_post"}
    queue_file = VAULT_DIR / 'Logs' / 'linkedin_queue.json'
    queue_file.parent.mkdir(exist_ok=True)
    if queue_file.exists():
        try:
            with open(queue_file, 'r') as f:
                queue = json.load(f)
        except (json.JSONDecodeError, ValueError):
            queue = []
    else:
        queue = []
    queue.append(queue_entry)
    with open(queue_file, 'w') as f:
        json.dump(queue, f, indent=2)
    dashboard_file = VAULT_DIR / 'Dashboard.md'
    if dashboard_file.exists():
        with open(dashboard_file, 'r') as f:
            dashboard_content = f.read()
        if "LinkedIn post ready for manual posting" not in dashboard_content:
            with open(dashboard_file, 'a') as f:
                f.write(f"\n\n## Notifications\n- LinkedIn post ready for manual posting - check Logs/linkedin_queue.json")
    return {"id": f"simulated_{len(queue)}", "status": "queued"}

def log_action(action, filename, details=None):
    today = datetime.now().strftime('%Y-%m-%d')
    logs_dir = VAULT_DIR / 'Logs'
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / f"{today}.json"
    log_entry = {"timestamp": datetime.now().isoformat(), "action": action, "filename": filename, "details": details}
    logs = []
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                content = f.read().strip()
                if content:
                    logs = json.loads(content)
                    if not isinstance(logs, list):
                        logs = []
        except (json.JSONDecodeError, ValueError):
            logs = []
    logs.append(log_entry)
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)

def move_file(source_path, destination_folder):
    dest_path = VAULT_DIR / destination_folder / source_path.name
    dest_path.parent.mkdir(exist_ok=True)
    shutil.move(str(source_path), str(dest_path))
    return dest_path

def process_markdown_file(file_path):
    file_path = Path(file_path)
    try:
        frontmatter, content = read_markdown_with_frontmatter(file_path)
        if frontmatter and frontmatter.get('type') == 'linkedin_post':
            print(f"Processing LinkedIn post: {file_path.name}")
            post_body = content.strip()
            if not post_body:
                raise ValueError("No content found in markdown file")
            result = post_to_linkedin(post_body)
            print(f"LinkedIn result: {result.get('status')} — ID: {result.get('id')}")
            done_path = move_file(file_path, 'Done')
            log_action('linkedin_post_success', file_path.name, {'post_id': result.get('id'), 'status': result.get('status'), 'destination': str(done_path)})
            return True
        else:
            print(f"File {file_path.name} is not a LinkedIn post - skipping (handled by approval_watcher)")
            return True  # Return True so it gets added to processed_files and ignored
    except Exception as e:
        print(f"Error processing {file_path.name}: {str(e)}")
        failed_path = move_file(file_path, 'Failed')
        log_action('linkedin_post_failed', file_path.name, {'error': str(e), 'destination': str(failed_path)})
        return False

def main():
    approved_folder = VAULT_DIR / 'Approved'
    if not approved_folder.exists():
        print(f"Error: {approved_folder} does not exist")
        return
    print(f"Watching folder: {approved_folder}")
    processed_files = set()
    try:
        while True:
            md_files = list(approved_folder.glob('*.md'))
            for file_path in md_files:
                if file_path not in processed_files:
                    print(f"New file detected: {file_path.name}")
                    success = process_markdown_file(file_path)
                    if success:
                        processed_files.add(file_path)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopping the watcher...")

if __name__ == "__main__":
    main()
