import requests, os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('GITHUB_TOKEN')
repo = os.getenv('GITHUB_REPO')
headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github+json'
}

r = requests.get(f'https://api.github.com/repos/{repo}/git/refs/heads/main', headers=headers)
data = r.json()
print("SHA:", data['object']['sha'])