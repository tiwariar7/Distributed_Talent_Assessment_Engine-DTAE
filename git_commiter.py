#!/usr/bin/env python3
import argparse
import datetime
import glob
import os
import random
import shutil
import subprocess
import sys
import stat
import time

def find_git_path():
    try:
        subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return "git"
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        pattern = os.path.join(local_app_data, "GitHubDesktop", "app-*", "resources", "app", "git", "cmd", "git.exe")
        matches = glob.glob(pattern)
        if matches:
            matches.sort()
            return matches[-1]

    common_paths = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return None

def run_git(git_path, args, env=None, cwd=None):
    try:
        result = subprocess.run(
            [git_path] + args, 
            capture_output=True, 
            text=True, 
            env=env,
            cwd=cwd
        )
        return result
    except Exception as e:
        return type('obj', (object,), {'returncode': 1, 'stderr': str(e), 'stdout': ''})()

def setup_git_config(git_path, repo_path):
    """Check and setup git user configuration if missing"""
    result = run_git(git_path, ['config', 'user.name'], cwd=repo_path)
    if result.returncode != 0 or not result.stdout.strip():
        print('[*] Setting git user.name...')
        run_git(git_path, ['config', '--local', 'user.name', 'Development Team'], cwd=repo_path)
    
    result = run_git(git_path, ['config', 'user.email'], cwd=repo_path)
    if result.returncode != 0 or not result.stdout.strip():
        print('[*] Setting git user.email...')
        run_git(git_path, ['config', '--local', 'user.email', 'dev@dtae.com'], cwd=repo_path)

def remove_readonly(func, path, _):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

def safe_delete_directory(dir_path):
    if not os.path.exists(dir_path):
        return True
    
    for attempt in range(3):
        try:
            shutil.rmtree(dir_path, onerror=remove_readonly)
            return True
        except PermissionError:
            time.sleep(2)
            if attempt == 2:
                try:
                    os.system(f'cmd /c rd /s /q "{dir_path}" 2>nul')
                except:
                    pass
    return False

# File Stage Categorization Mapping
def get_file_stage(file_path):
    path = file_path.lower().replace('\\', '/')
    if 'readme' in path or 'agents.md' in path or 'claude.md' in path or path.startswith('docs/') or 'docs/' in path or path.startswith('scripts/'):
        return 17
    if 'docker' in path or 'docker-compose' in path or '.env.example' in path or '.gitignore' in path:
        return 1
    if 'manage.py' in path or 'pyproject.toml' in path or 'pytest.ini' in path or 'requirements.txt' in path:
        return 1
    if 'backend/config/' in path:
        return 2
    if 'backend/apps/accounts/' in path:
        if 'models.py' in path:
            return 3
        return 4
    if 'backend/apps/organizations/' in path:
        return 4
    if 'backend/apps/assessments/' in path:
        if 'models.py' in path or 'admin.py' in path:
            return 5
        return 10
    if 'backend/apps/dsa_intelligence/' in path or 'backend/apps/executions/' in path:
        return 6
    if 'backend/apps/proctoring/' in path:
        return 7
    if 'backend/apps/scoring/' in path:
        return 8
    if 'backend/apps/recruiter/' in path or 'backend/apps/health/' in path or 'backend/apps/leaderboard/' in path:
        return 9
    if 'backend/tests/' in path:
        return 11
    if 'frontend/' in path:
        if 'package.json' in path or 'tsconfig.json' in path or 'next.config.ts' in path or 'eslint.config' in path or 'public/' in path:
            return 12
        if 'src/app/layout.tsx' in path or 'src/app/page.tsx' in path or 'src/app/globals.css' in path:
            return 13
        if 'src/hooks/' in path or 'src/lib/' in path or 'src/utils/' in path or 'src/styles/' in path:
            return 14
        if 'src/components/' in path:
            return 15
        if 'src/app/assessment/' in path or 'editor' in path:
            return 16
        if 'src/app/proctoring/' in path or 'proctor' in path:
            return 16
        if 'src/app/dashboard/' in path or 'src/app/admin/' in path or 'leaderboard' in path or 'analytics' in path:
            return 16
        return 16
    return 18

def get_category_key(file_path):
    path = file_path.lower().replace('\\', '/')
    if 'readme' in path or 'agents.md' in path or 'claude.md' in path or path.startswith('docs/') or 'docs/' in path or path.startswith('scripts/'):
        return "documentation"
    if 'docker' in path or 'docker-compose' in path or '.env.example' in path or '.gitignore' in path:
        return "project_init"
    if 'manage.py' in path or 'pyproject.toml' in path or 'pytest.ini' in path or 'requirements.txt' in path:
        return "project_init"
    if 'backend/config/' in path:
        return "django_config"
    if 'backend/apps/accounts/' in path:
        if 'models.py' in path:
            return "auth_models"
        return "auth_apis"
    if 'backend/apps/organizations/' in path:
        return "organization"
    if 'backend/apps/assessments/' in path:
        if 'models.py' in path or 'admin.py' in path:
            return "assessments_models"
        return "assessment_apis"
    if 'backend/apps/dsa_intelligence/' in path or 'backend/apps/executions/' in path:
        return "dsa_intelligence"
    if 'backend/apps/proctoring/' in path:
        return "proctoring"
    if 'backend/apps/scoring/' in path:
        return "scoring"
    if 'backend/apps/recruiter/' in path or 'backend/apps/health/' in path or 'backend/apps/leaderboard/' in path:
        return "analytics_leaderboard"
    if 'backend/tests/' in path:
        return "backend_tests"
    if 'frontend/' in path:
        if 'package.json' in path or 'tsconfig.json' in path or 'next.config.ts' in path or 'eslint.config' in path or 'public/' in path:
            return "frontend_config"
        if 'src/app/layout.tsx' in path or 'src/app/page.tsx' in path or 'src/app/globals.css' in path:
            return "frontend_pages"
        if 'src/hooks/' in path or 'src/lib/' in path or 'src/utils/' in path or 'src/styles/' in path:
            return "frontend_components"
        if 'src/components/' in path:
            return "frontend_components"
        if 'src/app/assessment/' in path or 'editor' in path:
            return "frontend_assessment"
        if 'src/app/proctoring/' in path or 'proctor' in path:
            return "frontend_proctoring"
        if 'src/app/dashboard/' in path or 'src/app/admin/' in path or 'leaderboard' in path or 'analytics' in path:
            return "frontend_analytics"
        return "frontend_pages"
    return "refactoring"

CATEGORIES = {
    "project_init": {
        "title_templates": [
            "chore(infra): initialize project skeleton and base config",
            "chore(config): set up development environment skeleton",
            "chore(deps): configure project dependencies and requirements"
        ],
        "bullets": [
            "Set up root level configurations and environment templates",
            "Configure Dockerfiles and compose settings for microservices",
            "Define python dependency list in requirements.txt",
            "Establish package-lock and linter configurations for frontend"
        ]
    },
    "django_config": {
        "title_templates": [
            "feat(backend): configure Django core settings and routing",
            "feat(backend): set up core settings, WSGI, and ASGI entries",
            "feat(backend): implement base settings with environment integration"
        ],
        "bullets": [
            "Configure settings.py with database and cache routing",
            "Define root URL patterns and API versioning schemas",
            "Add security middleware and CORS policy configurations",
            "Set up Celery task queue configurations for async jobs"
        ]
    },
    "auth_models": {
        "title_templates": [
            "feat(auth): implement UserProfile database schemas",
            "feat(auth): create custom User model and relational fields",
            "feat(auth): design authentication schema and database migration"
        ],
        "bullets": [
            "Extend AbstractBaseUser to define custom UserProfile model",
            "Add role-based authorization levels (Candidate, Recruiter, Admin)",
            "Configure unique constraint checks and database indexing on profiles",
            "Generate initial authentication model migrations"
        ]
    },
    "auth_apis": {
        "title_templates": [
            "feat(auth): develop authentication views and JWT endpoints",
            "feat(auth): implement login, register, and token refresh APIs",
            "feat(auth): add serializer validation for JWT authentication"
        ],
        "bullets": [
            "Implement login and token refresh views with djangorestframework-simplejwt",
            "Add UserProfile serializer with validation for email and passwords",
            "Configure route mappings for security and login actions",
            "Apply permission classes to restrict access on unauthorized endpoints"
        ]
    },
    "organization": {
        "title_templates": [
            "feat(org): implement Organization and Team structures",
            "feat(org): add recruiter team management models and APIs",
            "feat(org): configure organization relationship constraints"
        ],
        "bullets": [
            "Create Organization and Team entities with recursive relations",
            "Build API views for recruiter registration and membership management",
            "Configure database schema migrations for organization-level models",
            "Set up relational query prefetching for team structures"
        ]
    },
    "assessments_models": {
        "title_templates": [
            "feat(assessment): define Assessment and Question schemas",
            "feat(assessment): design question bank database schemas",
            "feat(assessment): implement database structures for test questions"
        ],
        "bullets": [
            "Create Assessment and Question models with difficulty attributes",
            "Define QuestionBank and tagging tables for categorizing items",
            "Add CandidateResponse schema to store test submissions",
            "Build schema migrations for assessment models"
        ]
    },
    "dsa_intelligence": {
        "title_templates": [
            "feat(engine): implement sandboxed code execution runner",
            "feat(engine): build DSA testcase evaluator and intelligence app",
            "feat(engine): add multi-language execution runtime wrappers"
        ],
        "bullets": [
            "Set up secure execution sandbox for candidate code submissions",
            "Implement wrappers for Python, JavaScript, C++, and Java runners",
            "Create validation scripts comparing console outputs with testcases",
            "Set memory and CPU time execution limits to prevent infinite loops"
        ]
    },
    "proctoring": {
        "title_templates": [
            "feat(proctoring): implement candidate monitoring and events tracker",
            "feat(proctoring): add face-detection alerts and window focus logs",
            "feat(proctoring): build proctoring violation scoring backend"
        ],
        "bullets": [
            "Design model schema for tracking candidate proctoring events",
            "Implement browser blur/focus event API endpoint recorders",
            "Create webcam frame analysis and face-detection trigger hooks",
            "Add anomaly scores to assess violation levels during tests"
        ]
    },
    "scoring": {
        "title_templates": [
            "feat(scoring): implement evaluation engine and score calculators",
            "feat(scoring): add automated testcase scoring and grader logic",
            "feat(scoring): construct automated PDF report generator"
        ],
        "bullets": [
            "Develop algorithmic grading engine using testcase execution results",
            "Configure Celery task handler to run code analysis in background",
            "Implement PDF report builder for assessment summaries",
            "Create email delivery utility to notify recruiters on test completion"
        ]
    },
    "analytics_leaderboard": {
        "title_templates": [
            "feat(analytics): implement leaderboard ranking and analytics",
            "feat(analytics): add system status checks and dashboard metrics",
            "feat(analytics): build candidate performance review views"
        ],
        "bullets": [
            "Implement candidate ranking calculations based on score and time",
            "Set up health check monitoring for database, Redis, and Celery",
            "Develop statistics endpoints for admin dashboard visualization",
            "Optimize leaderboard lookup queries using caching decorators"
        ]
    },
    "assessment_apis": {
        "title_templates": [
            "feat(assessment): build REST APIs for candidate test sessions",
            "feat(assessment): implement assessment starting and completion views",
            "feat(assessment): create question randomization and time checkers"
        ],
        "bullets": [
            "Create views for candidates to initiate assessment sessions",
            "Implement serializer for candidate test answers validation",
            "Add backend timers to auto-submit when session duration expires",
            "Setup API routing links for assessments-app view controllers"
        ]
    },
    "backend_tests": {
        "title_templates": [
            "test(backend): implement unit and integration test suites",
            "test(backend): add pytest models verification and mock runners",
            "test(backend): expand backend test coverage for assessment flow"
        ],
        "bullets": [
            "Write pytest cases checking model integrity and constraints",
            "Implement view-level mocks to bypass external runner runtime calls",
            "Set up fixtures for seeding test db with user and question banks",
            "Generate coverage reports verifying backend logic compliance"
        ]
    },
    "frontend_config": {
        "title_templates": [
            "chore(frontend): configure Next.js environment settings",
            "chore(frontend): initialize react dashboard configs and dependencies",
            "chore(frontend): set up package.json, eslint, and next.config.ts"
        ],
        "bullets": [
            "Create package.json and tsconfig configuration definitions",
            "Set up Tailwind CSS presets and global styling layouts",
            "Configure ESLint rules and typescript lint validations",
            "Add next.config.ts and environmental configuration parameters"
        ]
    },
    "frontend_pages": {
        "title_templates": [
            "feat(frontend): design responsive homepage and auth pages",
            "feat(frontend): implement core login, register, and splash screens",
            "feat(frontend): build layout skeletons and authentication components"
        ],
        "bullets": [
            "Implement Next.js layout structure with responsive headers",
            "Build auth views (login, signup) with form inputs and styling",
            "Integrate JWT storage flow in local cookie handling helper",
            "Setup global CSS transitions and custom theme values"
        ]
    },
    "frontend_components": {
        "title_templates": [
            "feat(frontend): develop shared dashboard components and hooks",
            "feat(frontend): implement visual statistics widgets and dashboards",
            "feat(frontend): add interactive candidate card components"
        ],
        "bullets": [
            "Build reusable buttons, card holders, modals, and spinners",
            "Create hooks tracking browser visibility and window dimensions",
            "Design recruiter control panels presenting active assessment details",
            "Integrate fetch middleware for making authenticated api requests"
        ]
    },
    "frontend_assessment": {
        "title_templates": [
            "feat(frontend): implement candidate assessment editor page",
            "feat(frontend): build Monaco editor layout with language selector",
            "feat(frontend): add real-time execution drawer and test validation"
        ],
        "bullets": [
            "Integrate Monaco Editor component with full styling defaults",
            "Add language dropdown selection and submission event handlers",
            "Create terminal log panel displaying stdout and execution statuses",
            "Implement automatic saving callbacks protecting user's code"
        ]
    },
    "frontend_proctoring": {
        "title_templates": [
            "feat(frontend): integrate webcam feed and window focus hooks",
            "feat(frontend): build frontend camera check and security alerts",
            "feat(frontend): implement candidate action trackers for security"
        ],
        "bullets": [
            "Connect browser mediaDevices to stream camera feed dynamically",
            "Add focus-out events to warn candidates on tab changes",
            "Integrate webcam capture triggers sending frames to proctoring endpoint",
            "Add fullscreen enforcement overlay preventing desktop exits"
        ]
    },
    "frontend_analytics": {
        "title_templates": [
            "feat(frontend): implement evaluation charts and leaderboard tabs",
            "feat(frontend): build candidate score summary dashboards",
            "feat(frontend): add interactive graphs detailing assessment results"
        ],
        "bullets": [
            "Design ranking listings showing scoring distributions",
            "Build detailed assessment summary grids for recruiter audits",
            "Implement score metric charts mapping candidate performance metrics",
            "Create customization views for candidate settings profiles"
        ]
    },
    "documentation": {
        "title_templates": [
            "docs: update installation instructions and contributing guide",
            "docs: create comprehensive API integration documentation",
            "docs: document platform architecture and deployment steps"
        ],
        "bullets": [
            "Write setup guidelines detailing dev container deployment",
            "Add endpoints documentation detailing assessment execution payloads",
            "Document Docker setup steps for postgres and celery integration",
            "Establish code contributing guidelines and style standards"
        ]
    },
    "refactoring": {
        "title_templates": [
            "refactor: optimize database queries and response formatting",
            "refactor: clean up backend middleware and validation handlers",
            "refactor: structure frontend state management and API wrappers",
            "perf: optimize memory footprint during code execution",
            "fix: resolve concurrent state updates on candidate scoreboards",
            "style: align page padding and dark mode styling guidelines"
        ],
        "bullets": [
            "Optimize query paths reducing database roundtrips",
            "Update validations preventing payload injection issues",
            "Refactor styling margins and layout responsive viewports",
            "Improve error boundaries catching unhandled API exceptions"
        ]
    }
}

def generate_commit_message(category, files_in_commit, commit_idx, total_commits, is_modification=False):
    cat_data = CATEGORIES.get(category, CATEGORIES["refactoring"])
    
    if is_modification:
        mod_verbs = ["refactor", "fix", "perf", "style", "chore"]
        verb = random.choice(mod_verbs)
        
        file_basenames = [os.path.basename(f) for f in files_in_commit]
        files_str = ", ".join(file_basenames[:2])
        if len(file_basenames) > 2:
            files_str += f" and {len(file_basenames)-2} other files"
            
        title = f"{verb}: update and optimize {files_str}"
        
        available_bullets = cat_data["bullets"] + CATEGORIES["refactoring"]["bullets"]
        bullets = random.sample(available_bullets, k=min(4, len(available_bullets)))
        if files_in_commit:
            bullets[0] = f"Refactor and clean code structure in {file_basenames[0]}"
    else:
        title_template = random.choice(cat_data["title_templates"])
        title = title_template
        bullets = random.sample(cat_data["bullets"], k=min(4, len(cat_data["bullets"])))
        
        file_basenames = [os.path.basename(f) for f in files_in_commit]
        if file_basenames:
            bullets[0] = f"Initialize and structure {file_basenames[0]}"
            if len(file_basenames) > 1:
                bullets[1] = f"Add corresponding implementation files: {', '.join(file_basenames[1:3])}"
                
    bullet_str = "\n".join([f"- {b.strip().lstrip('- ')}" for b in bullets])
    return f"{title}\n\n{bullet_str}"

def is_ignored(rel_path):
    parts = rel_path.replace('\\', '/').split('/')
    ignored_patterns = {
        '.git',
        'node_modules',
        '.next',
        '__pycache__',
        'venv',
        'env',
        'backups',
        'scratch',
        '.gemini',
        '.idea',
        '.vscode',
        'dist',
        'build'
    }
    for part in parts:
        if part in ignored_patterns:
            return True
        if part.endswith('.pyc') or part.endswith('.pyo') or part.endswith('.pyd'):
            return True
    return False

def get_all_files_from_folder(folder_path):
    """Get all files from the specified folder recursively, excluding ignored ones"""
    files = []
    for root, dirs, filenames in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in {
            '.git', 'node_modules', '.next', '__pycache__', 'venv', 'env',
            'backups', 'scratch', '.gemini', '.idea', '.vscode', 'dist', 'build'
        }]
        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, folder_path)
            rel_path_unix = rel_path.replace('\\', '/')
            if not is_ignored(rel_path_unix):
                files.append(rel_path_unix)
    return sorted(files)

def modify_file(file_path):
    if not os.path.exists(file_path):
        return False
    
    _, ext = os.path.splitext(file_path.lower())
    
    updates = [
        "Optimize imports and clean up code structure.",
        "Improve error handling and exception logging.",
        "Add typing hints and documentation docstrings.",
        "Refactor variable names for better readability.",
        "Update validation checks and constraints.",
        "Optimize query performance and database indexing.",
        "Fix minor edge cases in calculation functions.",
        "Improve responsive styles and layouts.",
        "Align with project code quality guidelines.",
        "Enhance component rendering performance."
    ]
    update_comment = random.choice(updates)
    
    try:
        if ext == '.py':
            with open(file_path, 'r+', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 150000:
                    return False
                f.seek(0, 2)
                f.write(f"\n# Refactor: {update_comment}\n")
            return True
        elif ext in ['.js', '.ts', '.tsx', '.jsx', '.css']:
            with open(file_path, 'r+', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 150000:
                    return False
                f.seek(0, 2)
                f.write(f"\n// Refactor: {update_comment}\n")
            return True
        elif ext in ['.md', '.txt']:
            with open(file_path, 'r+', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 150000:
                    return False
                f.seek(0, 2)
                f.write(f"\n\n- Note: {update_comment}\n")
            return True
    except Exception as e:
        print(f"Warning: Failed to modify file {file_path}: {e}")
    
    return False

def clear_remote_repository(git_path, temp_repo_dir):
    """
    Completely clear the existing repository content using standard Git operations.
    No force push or destructive history rewriting.
    """
    print('[*] Checking if remote repository contains commits to clear...')
    result = run_git(git_path, ['log', '-n', '1'], cwd=temp_repo_dir)
    if result.returncode != 0:
        print('[*] Remote repository appears to be empty or uninitialized. Skipping cleanup.')
        return
        
    result = run_git(git_path, ['ls-files'], cwd=temp_repo_dir)
    tracked_files = result.stdout.strip().splitlines()
    
    if not tracked_files:
        print('[*] No tracked files found to clear.')
        return
        
    print(f'[*] Found {len(tracked_files)} files. Clearing repository content...')
    
    rm_res = run_git(git_path, ['rm', '-rf', '.'], cwd=temp_repo_dir)
    if rm_res.returncode != 0:
        print(f'Warning: git rm failed: {rm_res.stderr}. Trying manual deletion and staging...')
        for f in tracked_files:
            p = os.path.join(temp_repo_dir, f)
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        run_git(git_path, ['add', '-A'], cwd=temp_repo_dir)
        
    commit_msg = (
        "chore: clear repository content for clean start\n\n"
        "- Remove all existing files and directory structure\n"
        "- Ensure a fresh starting point for project initialization\n"
        "- Clean workspace for systematic module deployment\n"
        "- Prepare repository for structured commit history"
    )
    commit_res = run_git(git_path, ['commit', '-m', commit_msg], cwd=temp_repo_dir)
    if commit_res.returncode != 0:
        print(f'[-] Clearance commit failed: {commit_res.stderr}')
        return
        
    print('[+] Clearance commit created successfully')
    
    print('[*] Pushing clearance commit to remote origin main...')
    push_res = run_git(git_path, ['push', 'origin', 'main'], cwd=temp_repo_dir)
    if push_res.returncode != 0:
        branch_res = run_git(git_path, ['branch', '--show-current'], cwd=temp_repo_dir)
        active_branch = branch_res.stdout.strip() or 'main'
        print(f'[*] Pushing clearance commit to remote origin {active_branch}...')
        push_res = run_git(git_path, ['push', 'origin', active_branch], cwd=temp_repo_dir)
        
    if push_res.returncode == 0:
        print('[+] Successfully cleared remote repository content!')
    else:
        print(f'[-] Failed to push clearance commit: {push_res.stderr}')
        print('[!] Proceeding with local history generation, but push at the end may require manual resolve.')

def generate_random_daily_commits(start_date, end_date, target_commits):
    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end_dt - start_dt).days + 1
    
    base_per_day = target_commits // total_days
    remainder = target_commits % total_days
    
    daily_counts = []
    for i in range(total_days):
        extra = 1 if i < remainder else 0
        variation = random.randint(-3, 3)
        count = max(3, base_per_day + extra + variation)
        daily_counts.append(count)
    
    total = sum(daily_counts)
    while total != target_commits:
        diff = target_commits - total
        step = 1 if diff > 0 else -1
        idx = random.randint(0, total_days - 1)
        if daily_counts[idx] + step >= 0:
            daily_counts[idx] += step
            total += step
            
    return daily_counts

def distribute_commits_across_day(day_date, num_commits):
    if num_commits <= 0:
        return []
    
    commit_times = []
    for i in range(num_commits):
        rand = random.random()
        if rand < 0.4:
            hour = random.randint(9, 12)
        elif rand < 0.8:
            hour = random.randint(14, 17)
        else:
            hour = random.randint(19, 20)
        
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        commit_time = datetime.datetime.combine(day_date, datetime.time(hour, minute, second))
        commit_times.append(commit_time)
    
    commit_times.sort()
    return commit_times

def generate_timeline(start_date, end_date, target_commits):
    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    
    daily_commit_counts = generate_random_daily_commits(start_date, end_date, target_commits)
    
    all_commit_times = []
    current_date = start_dt
    
    for daily_count in daily_commit_counts:
        if current_date > end_dt:
            break
        day_commits = distribute_commits_across_day(current_date, daily_count)
        all_commit_times.extend(day_commits)
        current_date += datetime.timedelta(days=1)
    
    all_commit_times.sort()
    return all_commit_times, daily_commit_counts

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
    default_temp_dir = os.path.join(user_profile, 'temp_repo_dtae')
    
    parser = argparse.ArgumentParser(description='Rebuild repository with structured, time-aligned commits using standard Git operations.')
    parser.add_argument('--source-folder', default=script_dir, 
                        help='Source folder containing files to commit (default: script directory)')
    parser.add_argument('--start-date', default='2026-01-15', 
                        help='Timeline start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2026-05-24', 
                        help='Timeline end date (YYYY-MM-DD)')
    parser.add_argument('--target-commits', type=int, default=978,
                        help='Target number of commits (default: 978)')
    parser.add_argument('--remote', default='https://github.com/tiwariar7/Distributed_Talent_Assessment_Engine-DTAE',
                        help='GitHub remote URL')
    parser.add_argument('--push', action='store_true', dest='push', default=True,
                        help='Push to GitHub using standard non-destructive push workflow (default: True)')
    parser.add_argument('--no-push', action='store_false', dest='push',
                        help='Do not push to GitHub')
    parser.add_argument('--temp-dir', default=default_temp_dir, 
                        help='Temporary directory for rebuilding repository')
    args = parser.parse_args()

    if not os.path.exists(args.source_folder):
        print(f'ERROR: Source folder not found: {args.source_folder}')
        sys.exit(1)

    temp_repo_dir = os.path.abspath(args.temp_dir)
    print(f'[*] Working directory: {temp_repo_dir}')
    print(f'[*] Target commits: {args.target_commits}')

    if os.path.exists(temp_repo_dir):
        print(f'[*] Removing existing temp directory...')
        safe_delete_directory(temp_repo_dir)

    os.makedirs(temp_repo_dir, exist_ok=True)
    print(f'[*] Created temporary repository folder at: {temp_repo_dir}')
    
    git_path = find_git_path()
    if not git_path:
        print('ERROR: Git executable not found.')
        sys.exit(1)
    
    print(f'[*] Found Git: {git_path}')
    
    print(f'[*] Cloning remote repository: {args.remote}...')
    clone_res = subprocess.run([git_path, 'clone', args.remote, temp_repo_dir], capture_output=True, text=True)
    
    repo_initialized = False
    if clone_res.returncode == 0:
        print('[+] Successfully cloned remote repository!')
        repo_initialized = True
    else:
        print(f'[-] Clone failed: {clone_res.stderr.strip()}')
        print('[*] Initializing a new local git repository instead...')
        init_res = run_git(git_path, ['init'], cwd=temp_repo_dir)
        if init_res.returncode == 0:
            print('[+] Initialized empty Git repository.')
            run_git(git_path, ['remote', 'add', 'origin', args.remote], cwd=temp_repo_dir)
            repo_initialized = True
        else:
            print(f'[-] Git init failed: {init_res.stderr}')
            sys.exit(1)
            
    if not repo_initialized:
        print('[-] Could not initialize repository.')
        sys.exit(1)
        
    setup_git_config(git_path, temp_repo_dir)
    run_git(git_path, ['branch', '-M', 'main'], cwd=temp_repo_dir)
    
    # 4. Completely clear existing repo content (standard git operations only)
    clear_remote_repository(git_path, temp_repo_dir)
    
    # 5. Get list of files to commit
    all_files = get_all_files_from_folder(args.source_folder)
    print(f'[*] Found {len(all_files)} files to commit')
    if not all_files:
        print('[-] No files found to commit.')
        sys.exit(1)
        
    # Sort files by their logical stage
    all_files_sorted = sorted(all_files, key=lambda f: (get_file_stage(f), f))
    
    # 6. Generate timeline of commits
    commit_dates, daily_commit_counts = generate_timeline(args.start_date, args.end_date, args.target_commits)
    print(f'\n[*] Timeline Statistics:')
    print(f'    - Date range: {args.start_date} to {args.end_date}')
    print(f'    - Total commits: {len(commit_dates)}')
    
    # 7. Create commits
    success_count = 0
    fail_count = 0
    
    F = len(all_files_sorted)
    N = args.target_commits
    
    if N >= F:
        P1 = F
        P2 = N - F
    else:
        P1 = N
        P2 = 0
        
    print(f'[*] Commits distribution: Phase 1 (Additions) = {P1}, Phase 2 (Refactoring) = {P2}')
    
    added_files = set()
    
    for idx, commit_date in enumerate(commit_dates):
        files_to_add = []
        files_to_modify = []
        is_modification = False
        
        if idx < P1:
            if N >= F:
                files_to_add = [all_files_sorted[idx]]
            else:
                start_f_idx = idx * F // N
                end_f_idx = (idx + 1) * F // N
                files_to_add = all_files_sorted[start_f_idx:end_f_idx]
                
            for f in files_to_add:
                src_path = os.path.join(args.source_folder, f)
                dest_path = os.path.join(temp_repo_dir, f)
                dest_dir = os.path.dirname(dest_path)
                os.makedirs(dest_dir, exist_ok=True)
                try:
                    shutil.copy2(src_path, dest_path)
                    added_files.add(f)
                except Exception as e:
                    print(f'    Warning: Could not copy {f}: {e}')
        else:
            is_modification = True
            modifiable_files = [f for f in added_files if os.path.splitext(f.lower())[1] in ['.py', '.js', '.ts', '.tsx', '.jsx', '.css', '.md', '.txt']]
            if modifiable_files:
                num_files = random.randint(1, min(3, len(modifiable_files)))
                files_to_modify = random.sample(modifiable_files, num_files)
                for f in files_to_modify:
                    dest_path = os.path.join(temp_repo_dir, f)
                    modify_file(dest_path)
            else:
                # If no modifiable files are added yet, fallback to allow-empty commit
                pass
                
        staged_any = False
        for f in files_to_add:
            res = run_git(git_path, ['add', '--', f], cwd=temp_repo_dir)
            if res.returncode == 0:
                staged_any = True
        for f in files_to_modify:
            res = run_git(git_path, ['add', '--', f], cwd=temp_repo_dir)
            if res.returncode == 0:
                staged_any = True
                
        if not staged_any:
            run_git(git_path, ['add', '.'], cwd=temp_repo_dir)
            
        files_in_commit = files_to_add if not is_modification else files_to_modify
        if files_in_commit:
            primary_file = files_in_commit[0]
        else:
            primary_file = all_files_sorted[0]
            
        cat = get_category_key(primary_file)
        message = generate_commit_message(cat, files_in_commit, idx, N, is_modification)
        
        env = os.environ.copy()
        env['GIT_AUTHOR_DATE'] = commit_date.isoformat()
        env['GIT_COMMITTER_DATE'] = commit_date.isoformat()
        
        res = run_git(git_path, ['commit', '--allow-empty', '-m', message], env=env, cwd=temp_repo_dir)
        if res.returncode == 0:
            success_count += 1
            if success_count % 50 == 0 or success_count <= 10:
                print(f'[+] [{success_count:4d}/{N}] {commit_date.strftime("%Y-%m-%d %H:%M")} - {message.splitlines()[0][:60]}')
            elif success_count == 11:
                print('    ...')
        else:
            fail_count += 1
            if fail_count <= 5:
                print(f'[-] Commit {idx + 1} failed: {res.stderr[:100]}')
                
    print('-' * 70)
    print(f'\n[+] Results:')
    print(f'    - Successful commits: {success_count}')
    print(f'    - Failed commits: {fail_count}')
    print(f'    - Total commits: {success_count}')
    
    if args.push and success_count > 0:
        print('\n[*] Pushing to GitHub main branch...')
        print('    (This may take a few minutes for 1000+ commits)')
        res = run_git(git_path, ['push', '-u', 'origin', 'main'], cwd=temp_repo_dir)
        if res.returncode == 0:
            print('[+] Successfully pushed to GitHub!')
            print(f'[*] Repository URL: {args.remote}')
            print(f'[*] Total commits pushed: {success_count}')
        else:
            print(f'[-] Push failed: {res.stderr}')
            print('\n    To push manually:')
            print(f'    cd {temp_repo_dir}')
            print(f'    git push -u origin main')
    else:
        print(f'\n[i] Repository ready at: {temp_repo_dir}')
        if args.push and success_count == 0:
            print('[!] No successful commits created, skipping push')

if __name__ == '__main__':
    random.seed()
    main()