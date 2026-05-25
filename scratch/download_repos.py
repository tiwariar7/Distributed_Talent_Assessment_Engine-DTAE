import urllib.request
import zipfile
import io
import os

REPOS = [
    ("snehasishroy-leetcode", "https://github.com/snehasishroy/leetcode-companywise-interview-questions/archive/refs/heads/master.zip"),
    ("liquidslr-problems", "https://github.com/liquidslr/interview-company-wise-problems/archive/refs/heads/master.zip")
]

def download_and_extract():
    os.makedirs("scratch", exist_ok=True)
    for name, url in REPOS:
        print(f"Downloading {name} from {url}...")
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req) as response:
                zip_data = response.read()
            print(f"Downloaded {len(zip_data)} bytes. Extracting...")
            with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                z.extractall("scratch")
            print(f"Successfully extracted {name}.")
        except Exception as e:
            print(f"Error downloading {name}: {e}")

if __name__ == "__main__":
    download_and_extract()
