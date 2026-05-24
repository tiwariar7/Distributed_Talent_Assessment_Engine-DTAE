import os
import re
import csv
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.utils.text import slugify
from apps.dsa_intelligence.models import Company, Topic, DSAQuestion, QuestionCompanyFrequency, FrequencyBucket

class Command(BaseCommand):
    help = "Ingest, normalize, and deduplicate DSA questions from scraped repositories."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of directories/files processed for testing (0 for unlimited)",
        )

    def normalize_title(self, title: str) -> str:
        """
        Normalize title to a canonical slug: lowercase, replace spaces/dashes,
        remove common suffixes like ' lc' or ' leetcode', remove punctuation.
        """
        t = title.lower().strip()
        t = re.sub(r'\s+lc\b|\s+leetcode\b', '', t)
        t = re.sub(r'[^a-z0-9\s\-]', '', t)
        t = re.sub(r'[\s\-]+', '-', t)
        return t.strip('-')

    def parse_float(self, value: str) -> float:
        """Parse percentage string or float string to float."""
        if not value:
            return 0.0
        val = value.replace("%", "").strip()
        try:
            f_val = float(val)
            # If it's a rate like 0.55, keep it, if it's 55.0% represent as 55.0
            return f_val
        except ValueError:
            return 0.0

    def clean_company_name(self, folder_name: str) -> tuple[str, str]:
        """Convert folder name to (name, slug)."""
        slug = slugify(folder_name)
        # convert 'google' to 'Google', 'bank-of-america' to 'Bank of America'
        name = folder_name.replace("-", " ").replace("_", " ").title()
        return name, slug

    def handle(self, *args, **options):
        limit = options["limit"]
        self.stdout.write(self.style.SUCCESS("Starting DSA Question Ingestion..."))

        # Base paths
        repo1_dir = "scratch/leetcode-companywise-interview-questions-master"
        repo2_dir = "scratch/interview-company-wise-problems-main"

        # Check path existence
        if not os.path.exists(repo1_dir) and not os.path.exists(repo2_dir):
            self.stdout.write(self.style.ERROR("Scraped repositories not found in scratch/."))
            return

        # Preload existing database models for faster in-memory lookups
        companies_cache = {c.slug: c for c in Company.objects.all()}
        topics_cache = {t.slug: t for t in Topic.objects.all()}
        
        # We cache DSA questions by URL and slug
        questions_by_url = {}
        questions_by_slug = {}
        for q in DSAQuestion.objects.all().prefetch_related("topics"):
            if q.leetcode_url:
                questions_by_url[q.leetcode_url.lower().rstrip("/")] = q
            questions_by_slug[q.slug] = q

        stats = {
            "companies_created": 0,
            "topics_created": 0,
            "questions_created": 0,
            "mappings_created": 0,
        }

        # Frequency mapping dictionaries
        repo1_freq_map = {
            "thirty-days.csv": FrequencyBucket.THIRTY_DAYS,
            "three-months.csv": FrequencyBucket.THREE_MONTHS,
            "six-months.csv": FrequencyBucket.SIX_MONTHS,
            "more-than-six-months.csv": FrequencyBucket.MORE_THAN_SIX_MONTHS,
            "all.csv": FrequencyBucket.ALL,
        }

        repo2_freq_map = {
            "1. Thirty Days.csv": FrequencyBucket.THIRTY_DAYS,
            "2. Three Months.csv": FrequencyBucket.THREE_MONTHS,
            "3. Six Months.csv": FrequencyBucket.SIX_MONTHS,
            "4. More Than Six Months.csv": FrequencyBucket.MORE_THAN_SIX_MONTHS,
            "5. All.csv": FrequencyBucket.ALL,
        }

        @transaction.atomic
        def save_frequency(question, company, bucket, frequency_val, repo, diff, tags_str):
            freq_obj, created = QuestionCompanyFrequency.objects.update_or_create(
                question=question,
                company=company,
                frequency_bucket=bucket,
                defaults={
                    "frequency_percentage": frequency_val,
                    "source_repo": repo,
                    "metadata": {
                        "difficulty": diff,
                        "tags": [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
                    }
                }
            )
            if created:
                stats["mappings_created"] += 1

        # Process Repo 1: leetcode-companywise-interview-questions-master
        if os.path.exists(repo1_dir):
            self.stdout.write("Processing leetcode-companywise repository...")
            subdirs = [
                d for d in os.listdir(repo1_dir)
                if os.path.isdir(os.path.join(repo1_dir, d)) and not d.startswith(".")
            ]
            if limit > 0:
                subdirs = subdirs[:limit]

            for folder in subdirs:
                comp_name, comp_slug = self.clean_company_name(folder)
                
                if comp_slug not in companies_cache:
                    try:
                        company, created = Company.objects.get_or_create(
                            slug=comp_slug,
                            defaults={"name": comp_name}
                        )
                        if created:
                            stats["companies_created"] += 1
                    except IntegrityError:
                        company = Company.objects.filter(slug=comp_slug).first() or Company.objects.filter(name=comp_name).first()
                    if company:
                        companies_cache[comp_slug] = company
                else:
                    company = companies_cache[comp_slug]

                comp_path = os.path.join(repo1_dir, folder)
                for file_name in os.listdir(comp_path):
                    if file_name in repo1_freq_map:
                        bucket = repo1_freq_map[file_name]
                        csv_path = os.path.join(comp_path, file_name)
                        
                        try:
                            with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                                reader = csv.DictReader(f)
                                for row in reader:
                                    # Columns: ID,URL,Title,Difficulty,Acceptance %,Frequency %
                                    title = row.get("Title")
                                    url = row.get("URL")
                                    difficulty = row.get("Difficulty", "Medium").title()
                                    acc_rate = self.parse_float(row.get("Acceptance %", "0.0"))
                                    freq_pct = self.parse_float(row.get("Frequency %", "0.0"))
                                    
                                    if not title:
                                        continue
                                        
                                    clean_slug = self.normalize_title(title)
                                    clean_url = url.lower().rstrip("/") if url else ""
                                    
                                    # Deduplication lookup
                                    question = None
                                    if clean_url and clean_url in questions_by_url:
                                        question = questions_by_url[clean_url]
                                    elif clean_slug in questions_by_slug:
                                        question = questions_by_slug[clean_slug]
                                        
                                    if not question:
                                        try:
                                            question, created = DSAQuestion.objects.get_or_create(
                                                slug=clean_slug,
                                                defaults={
                                                    "title": title,
                                                    "leetcode_url": url,
                                                    "difficulty": difficulty,
                                                    "acceptance_rate": acc_rate,
                                                }
                                            )
                                            if created:
                                                stats["questions_created"] += 1
                                        except IntegrityError:
                                            question = DSAQuestion.objects.filter(slug=clean_slug).first()
                                            if not question and url:
                                                question = DSAQuestion.objects.filter(leetcode_url__iexact=url).first()
                                        
                                        if question:
                                            questions_by_slug[clean_slug] = question
                                            if clean_url:
                                                questions_by_url[clean_url] = question
                                        
                                    save_frequency(
                                        question=question,
                                        company=company,
                                        bucket=bucket,
                                        frequency_val=freq_pct,
                                        repo="leetcode-companywise",
                                        diff=difficulty,
                                        tags_str=""
                                    )
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"Error reading {csv_path}: {e}"))

        # Process Repo 2: interview-company-wise-problems-main
        if os.path.exists(repo2_dir):
            self.stdout.write("Processing interview-company-wise repository...")
            subdirs = [
                d for d in os.listdir(repo2_dir)
                if os.path.isdir(os.path.join(repo2_dir, d)) and not d.startswith(".")
            ]
            if limit > 0:
                subdirs = subdirs[:limit]

            for folder in subdirs:
                comp_name, comp_slug = self.clean_company_name(folder)
                
                if comp_slug not in companies_cache:
                    try:
                        company, created = Company.objects.get_or_create(
                            slug=comp_slug,
                            defaults={"name": comp_name}
                        )
                        if created:
                            stats["companies_created"] += 1
                    except IntegrityError:
                        company = Company.objects.filter(slug=comp_slug).first() or Company.objects.filter(name=comp_name).first()
                    if company:
                        companies_cache[comp_slug] = company
                else:
                    company = companies_cache[comp_slug]

                comp_path = os.path.join(repo2_dir, folder)
                for file_name in os.listdir(comp_path):
                    if file_name in repo2_freq_map:
                        bucket = repo2_freq_map[file_name]
                        csv_path = os.path.join(comp_path, file_name)
                        
                        try:
                            with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                                reader = csv.DictReader(f)
                                for row in reader:
                                    # Columns: Difficulty,Title,Frequency,Acceptance Rate,Link,Topics
                                    title = row.get("Title")
                                    url = row.get("Link")
                                    difficulty = row.get("Difficulty", "Medium").title()
                                    acc_rate = self.parse_float(row.get("Acceptance Rate", "0.0"))
                                    # Sometimes acceptance rate is like 0.557, convert to percent 55.7
                                    if acc_rate > 0.0 and acc_rate <= 1.0:
                                        acc_rate = acc_rate * 100.0
                                    freq_pct = self.parse_float(row.get("Frequency", "0.0"))
                                    topics_str = row.get("Topics", "")
                                    
                                    if not title:
                                        continue
                                        
                                    clean_slug = self.normalize_title(title)
                                    clean_url = url.lower().rstrip("/") if url else ""
                                    
                                    # Deduplication lookup
                                    question = None
                                    if clean_url and clean_url in questions_by_url:
                                        question = questions_by_url[clean_url]
                                    elif clean_slug in questions_by_slug:
                                        question = questions_by_slug[clean_slug]
                                        
                                    if not question:
                                        try:
                                            question, created = DSAQuestion.objects.get_or_create(
                                                slug=clean_slug,
                                                defaults={
                                                    "title": title,
                                                    "leetcode_url": url,
                                                    "difficulty": difficulty,
                                                    "acceptance_rate": acc_rate,
                                                }
                                            )
                                            if created:
                                                stats["questions_created"] += 1
                                        except IntegrityError:
                                            question = DSAQuestion.objects.filter(slug=clean_slug).first()
                                            if not question and url:
                                                question = DSAQuestion.objects.filter(leetcode_url__iexact=url).first()
                                        
                                        if question:
                                            questions_by_slug[clean_slug] = question
                                            if clean_url:
                                                questions_by_url[clean_url] = question

                                    # Associate Topics
                                    if topics_str:
                                        for t_name in topics_str.split(","):
                                            t_name = t_name.strip()
                                            if not t_name:
                                                continue
                                            t_slug = slugify(t_name)
                                            if t_slug not in topics_cache:
                                                try:
                                                    topic, created = Topic.objects.get_or_create(
                                                        slug=t_slug,
                                                        defaults={"name": t_name}
                                                    )
                                                    if created:
                                                        stats["topics_created"] += 1
                                                except IntegrityError:
                                                    topic = Topic.objects.filter(slug=t_slug).first() or Topic.objects.filter(name=t_name).first()
                                                if topic:
                                                    topics_cache[t_slug] = topic
                                            else:
                                                topic = topics_cache[t_slug]
                                            
                                            # Avoid duplicate topic mapping queries
                                            if topic not in question.topics.all():
                                                question.topics.add(topic)
                                        
                                    save_frequency(
                                        question=question,
                                        company=company,
                                        bucket=bucket,
                                        frequency_val=freq_pct,
                                        repo="interview-company-wise",
                                        diff=difficulty,
                                        tags_str=topics_str
                                    )
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"Error reading {csv_path}: {e}"))

        self.stdout.write(self.style.SUCCESS("Ingestion completed successfully!"))
        self.stdout.write(self.style.NOTICE(f"Stats: {stats}"))
