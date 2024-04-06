from ghapi.all import GhApi
from flask import Flask, request
from ai import build_howto
from ghapi.all import GhApi
import time
from jwt import PyJWT
import os

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
    repo_url = gen_repo_url(repository['full_name'])

    owner = repo_path_components[0]
    repo_name = repo_path_components[1]



    if BOG_NAME not in owner:
        print("Not a GTBog")
        return "Unauthorized"

    issue = body['issue']
    issue_id = issue['id']
    issue_title = issue['title']

    create_comment(owner, repo_name, issue_id, "Generating how-to...")
    comment_body = build_howto("BOG Developer", issue_title, gen_repo_url(repo_name))

    create_comment(owner, repo_name, issue_id, comment_body)
    return "Success"

def gen_repo_url(name):
    return f'https://github.com/{name}'

def create_comment(owner, repo, issue, comment):
    api = GhApi(token=gen_jwt())
    api.issues.create_comment(owner, repo, issue, comment)

def gen_jwt():
    payload = {
        # Issued at time
        'iat': int(time.time()),
        # JWT expiration time (10 minutes maximum)
        'exp': int(time.time()) + 600,
        # GitHub App's identifier
        'iss': APP_ID
    }
    jwt_ins = PyJWT()
    encoded_jwt = jwt_ins.encode(payload, SECRET, algorithm='RS256')
    return encoded_jwt
