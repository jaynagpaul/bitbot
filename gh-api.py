from ghapi.all import GhApi
from flask import Flask, request
from ai import build_howto
from ghapi.all import GhApi
import os

secret = os.getenv("GH_SECRET")

app = Flask(__name__)
api = GhApi(token=secret)

BITBOT_STR = "@samrat"
BOG_NAME = "GTBitsOfGood"

@app.route("/webhook", methods=['POST'])
def read_incoming_webhook():
    if request.headers['X-GitHub-Event'] != "issue_comment":
        return

    body = request.get_json()
    if body['action'] != 'created' or BITBOT_STR not in body['comment']['body']:
        return
    
    repository = body['repository']
    full_repo_subpath = repository['full_name']
    repo_path_components = full_repo_subpath.split('/')
    repo_url = gen_repo_url(repository['full_name'])

    owner = repo_path_components[0]
    repo_name = repo_path_components[1];

    if BOG_NAME not in repo_name:
        return

    user = body['comment']['user']
    name = body['name']

    issue = body['issue']
    issue_id = issue['id']
    issue_title = issue['title']

    comment_body = build_howto(name, issue_title, gen_repo_url(repo_name))

    create_comment(owner, repo_name, issue_id, comment_body)

def gen_repo_url(name):
    return f'https://github.com/{name}'

def create_comment(owner, repo, issue, comment):
    api.issues.create_comment(owner, repo, issue, comment)