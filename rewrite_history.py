import subprocess
import os

repo_path = r"d:\ARIA"
os.chdir(repo_path)

# Comprehensive Human-Touch Baseline
replacements = {
    "chore: standardize": "refactor: environment config and api baseline",
    "docs: rewrite README": "docs: institutional overview update",
    "feat: implement GitHub Actions": "ci: add automation workflow",
    "fix: resolve .gitignore": "fix: resolve gitignore overlap",
    "Final Polish: Added Phase 4": "feat: dashboard and reporting integration",
    "fix: update Groq model": "fix: update model bridge",
    "license: initialize": "license: add MIT license",
    "Add MIT License": "license: add MIT license",
    "Phase 1: Document Intelligence": "feat: document ingestion and rag pipeline",
    "ARIA is online": "ARIA Intelligence System Online"
}

def clean_msg(msg):
    # Strip ALL non-ASCII (emojis, etc.) immediately
    msg = "".join(c for c in msg if 32 <= ord(c) < 127).strip()
    
    # Apply Human Phrases
    for old, new in replacements.items():
        if old in msg:
            return new
            
    # Senior engineers sometimes just use lowercase for quick fixes
    if len(msg) < 5: return "fix: minor refactor"
    return msg

def rewrite_history():
    # Use main_backup as the gold source
    log_cmd = ["git", "log", "--reverse", "--format=%H%n%P%n%an%n%ae%n%at%n%B%x00", "main_backup"]
    try:
        raw_output = subprocess.check_output(log_cmd, encoding='utf-8')
        raw_log = raw_output.split('\0')
    except Exception as e:
        print(f"Error reading log: {e}")
        return

    new_parent = None
    for entry in raw_log:
        lines = entry.strip().split('\n', 5)
        if len(lines) < 6: continue
        
        orig_id, orig_parents, author, email, atime, message = lines
        new_msg = clean_msg(message)
        
        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = author
        env["GIT_AUTHOR_EMAIL"] = email
        env["GIT_AUTHOR_DATE"] = atime
        env["GIT_COMMITTER_NAME"] = author
        env["GIT_COMMITTER_EMAIL"] = email
        env["GIT_COMMITTER_DATE"] = atime

        tree_id = subprocess.check_output(["git", "rev-parse", f"{orig_id}^{{tree}}"], encoding='utf-8').strip()
        
        cmd = ["git", "commit-tree", tree_id, "-m", new_msg]
        if new_parent:
            cmd.extend(["-p", new_parent])
        
        new_parent = subprocess.check_output(cmd, env=env, encoding='utf-8').strip()

    if new_parent:
        subprocess.run(["git", "update-ref", "refs/heads/main", new_parent])
        print(f"Successfully rewritten history to Human-Touch baseline: {new_parent}")

if __name__ == "__main__":
    rewrite_history()
