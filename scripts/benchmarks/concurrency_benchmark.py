import os
import time
import django
import concurrent.futures
from statistics import mean

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
try:
    django.setup()
except Exception as e:
    print(f"Django setup warning: {e}")

from infrastructure.docker.executor import DockerCodeExecutor
from infrastructure.couchdb.client import CouchDBClient
from infrastructure.storage.client import MinioStorageClient

def benchmark_sandbox_starts():
    print("\n=== Benchmarking Sandbox Startup Latency ===")
    executor = DockerCodeExecutor()
    
    # 1. Cold Start
    start_time = time.perf_counter()
    res1 = executor.execute("print('Hello World')", "python")
    cold_duration = time.perf_counter() - start_time
    print(f"Cold Start duration: {cold_duration:.3f}s (Exit code: {res1.exit_code})")
    
    # 2. Warm Starts
    warm_durations = []
    for i in range(5):
        start_time = time.perf_counter()
        res = executor.execute("print('Hello World')", "python")
        duration = time.perf_counter() - start_time
        warm_durations.append(duration)
        print(f"Warm Start {i+1} duration: {duration:.3f}s (Exit code: {res.exit_code})")
    
    print(f"Average Warm Start: {mean(warm_durations):.3f}s")
    return cold_duration, mean(warm_durations)

def benchmark_couchdb_mvcc():
    print("\n=== Benchmarking CouchDB MVCC Conflict Handling ===")
    client = CouchDBClient()
    doc_id = "benchmark_mvcc_test_doc"
    
    # Clean up or recreate
    try:
        doc = client.get_document(doc_id)
        # delete or ignore
    except Exception:
        pass
        
    client.create_document(doc_id, {"type": "execution_log", "entries": []})
    
    # Concurrent appends to the SAME document to force MVCC conflicts
    num_threads = 8
    num_appends_per_thread = 5
    
    def worker(worker_id):
        conflicts = 0
        successes = 0
        for i in range(num_appends_per_thread):
            try:
                client.append_to_execution_log(
                    doc_id,
                    {"worker": worker_id, "index": i, "timestamp": time.time()}
                )
                successes += 1
            except Exception as e:
                print(f"Append failed: {e}")
        return successes

    start_time = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        results = [f.result() for f in futures]
    
    duration = time.perf_counter() - start_time
    total_appends = sum(results)
    print(f"Completed {total_appends} concurrent appends in {duration:.3f}s")
    print(f"Throughput: {total_appends / duration:.2f} appends/sec")
    
    # Clean up
    try:
        doc = client.get_document(doc_id)
        print(f"Final log entry count: {len(doc.get('entries', []))}")
    except Exception:
        pass

def benchmark_minio_storage():
    print("\n=== Benchmarking MinIO Storage Latency ===")
    try:
        client = MinioStorageClient()
    except Exception as e:
        print(f"Skipping MinIO benchmark: client init failed: {e}")
        return

    num_uploads = 10
    durations = []
    
    start_time = time.perf_counter()
    for i in range(num_uploads):
        key = f"benchmarks/test_upload_{i}.txt"
        content = f"Benchmark dummy content {i}"
        
        t_start = time.perf_counter()
        client.upload_file_content(key, content)
        durations.append(time.perf_counter() - t_start)
        
    total_duration = time.perf_counter() - start_time
    print(f"Uploaded {num_uploads} files in {total_duration:.3f}s")
    print(f"Average upload latency: {mean(durations):.3f}s")

if __name__ == "__main__":
    print("Starting DTAE Performance & Concurrency Benchmarks")
    try:
        benchmark_sandbox_starts()
    except Exception as e:
        print(f"Sandbox benchmark failed: {e}")
        
    try:
        benchmark_couchdb_mvcc()
    except Exception as e:
        print(f"CouchDB MVCC benchmark failed: {e}")
        
    try:
        benchmark_minio_storage()
    except Exception as e:
        print(f"MinIO benchmark failed: {e}")

# Refactor: Refactor variable names for better readability.
