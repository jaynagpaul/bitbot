from ghapi.all import GhApi
from flask import Flask, request
from ai import build_howto
import time
from jwt import PyJWT
import os
from dotenv import load_dotenv
import requests

load_dotenv()

SECRET = os.getenv("GH_SECRET")
APP_ID = os.getenv("GH_APP_ID")

app = Flask(__name__)

BITBOT_STR = "samrat help"
BOG_NAME = "GTBitsOfGood"

@app.route("/webhook", methods=['POST'])
def read_incoming_webhook():
    if request.headers['X-GitHub-Event'] != "issue_comment":
        print("not a comment")
        return "not a comment"

    body = request.get_json()
    if body['action'] != 'created' or BITBOT_STR not in body['comment']['body']:
        print("dont care")
        return "Don't care"
    
    repository = body['repository']
    full_repo_subpath = repository['full_name']
    repo_path_components = full_repo_subpath.split('/')
    repo_url = gen_repo_url(full_repo_subpath)

    print(f'repo url: {repo_url}')

    owner = repo_path_components[0]
    repo_name = repo_path_components[1]



    if BOG_NAME not in owner:
        print("Not a GTBog")
        return "Unauthorized"

    issue = body['issue']
    issue_id = issue['number']
    issue_title = issue['title']

    print(f'comment url: {get_comment_create_url(owner, repo_name, issue_id)}')
    create_comment(owner, repo_name, issue_id, "Generating how-to...")
    comment_body = build_howto("BOG Developer", issue_title, repo_url)

    create_comment(owner, repo_name, issue_id, comment_body)
    return "Success"

def gen_repo_url(name):
    return f'https://github.com/{name}'

def get_comment_create_url(owner, repo, issue):
    return f'https://api.github.com/repos/{owner}/{repo}/issues/{issue}/comments'

def get_installation_url(owner, repo):
    return f'https://api.github.com/repos/{owner}/{repo}/installation'

def get_access_token_url(installation_id):
    return f'https://api.github.com/app/installations/{installation_id}/access_tokens'

def get_jwt_header():
    return {
        'Authorization': f'Bearer {gen_jwt()}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28' 
    }

def get_access_token(installation_id):
    resp = requests.post(get_access_token_url(installation_id), headers=get_jwt_header())
    return resp.json()['token']

def create_comment(owner, repo, issue, comment):
    s = requests.Session()
    # Get id of installation
    installation_resp = s.get(get_installation_url(owner, repo), headers=get_jwt_header())
    print(f'install: {installation_resp.json()}')
    # Get the access token for this installation
    access_token = get_access_token(installation_resp.json()['id'])

    body = {
        'owner': 'samrat-bot-app',
        'repo': f'{owner}/{repo}',
        'issue_number': issue,
        'body': comment,
    }
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    resp = s.post(get_comment_create_url(owner, repo, issue), json=body, headers=headers)
    print(f'GH api response: {resp.text}')

def gen_jwt():
    payload = {
        # Issued at time
        'iat': int(time.time()),
        # JWT expiration time (10 minutes maximum)
        'exp': int(time.time()) + 500,
        # GitHub App's identifier
        'iss': int(APP_ID)
    }
    jwt_ins = PyJWT()
    encoded_jwt = jwt_ins.encode(payload, SECRET, algorithm='RS256')
    print(f'secret: {SECRET}')
    print(f'encoded: {encoded_jwt}')
    print(f'app_id: {APP_ID}')
    return encoded_jwt
