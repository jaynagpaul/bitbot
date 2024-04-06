from pathlib import Path
import shutil
from typing import Callable
from anthropic import Anthropic
import tempfile
import os
from os import PathLike
from git import Repo  # pip install gitpython


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def build_howto(dev_name: str, ticket_name: str, repo_url: str) -> str:
    code = _fetch_code(repo_url)
    return _gen_howto(dev_name, ticket_name, code)

def _gen_howto(dev_name: str, ticket_name: str, code: str) -> str:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f""" You are Samrat, a very talented senior developer working for the club Bits of Good. Bits of Good is a club that builds and maintains open-source software for nonprofits. You are given a ticket you are in charge of implementing. Additionally, you are given the entire codebase. Based on this, you should provide a step-by-step guide on how to implement the ticket.
You should be very specific and detailed in your response. The ticket is for {dev_name}. You should greet them and make your response useful and playful! Jokes are more than acceptable, and feel free to be quirky, but your number one priority is to be helpful with instructions on implementing the ticket. You should respond in markdown.

    Ticket Name: {ticket_name}
    Code: 
    {code}
    """

    resp = client.messages.create(
        model="claude-3-haiku-20240307", # check model
        max_tokens=2500, # check max_tokens
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return resp.content

def _clone_repo(git_url: str, output_dir: PathLike):
    Repo.clone_from(git_url, output_dir, depth=1)

def _create_gitignore_validator(gitignore: str) -> Callable[[PathLike], bool]:
    return lambda path: not any(path.match(pattern) for pattern in gitignore.split("\n") if pattern != "")

def _get_code(repo_dir: PathLike) -> str:
    should_read = _create_gitignore_validator(Path(repo_dir, ".gitignore").read_text())

    code_list = []
    for file in Path(repo_dir).glob("**/*"):
        if not file.is_file(): continue
        if not should_read(file): continue
        if file.name.startswith("."): continue

        try: 
            text = file.read_text()
        except:
            continue

        code_list.append(f"{str(file.relative_to(repo_dir))}:\n{text}")

    return "\n\n".join(code_list)
    

def _fetch_code(git_url: str) -> str:
    temp_dir = tempfile.mkdtemp()
    try:
        _clone_repo(git_url, temp_dir)
        code =  _get_code(temp_dir)
    finally:
        shutil.rmtree(temp_dir)

    return code

