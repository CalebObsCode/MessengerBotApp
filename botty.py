from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
API_URL = 'https://graph.facebook.com/v2.6/me/messages'


# configure the app webhook
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return str(challenge)
        return "400"

    else:
        data = json.loads(request.data)
        sender_psid = data['entry'][0]['messaging'][0]['sender']['id']
        for data in data['entry'][0]['messaging']:
            if data['message']:
                handle_message(sender_psid, data['message'])
            elif data['postback']:
                handle_postback(sender_psid, data['postback'])
        return "200"


class Bot(object):
    def __init__(self, access_token, api_url=API_URL):
        self.access_token = access_token
        self.api_url = api_url

    def send_message(self, psid, message, messaging_type="RESPONSE"):
        headers = {'Content-Type': 'application/json'}
        if isinstance(message, str):
            message = {'text': message}
        data = {
            'messaging_type': messaging_type,
            'recipient': {
                'id': psid
            },
            'message': message,
        }

        params = {'access_token': self.access_token}
        response = requests.post(self.api_url,
                                 headers=headers,
                                 params=params,
                                 data=json.dumps(data))
        print(response.content)


# get messages and handle them
def handle_message(sender_psid, recieved_message):
    if recieved_message.get('text'):
        message = recieved_message['text']
        call_send_API(sender_psid, f"you said: {message}")
    else:
        message = recieved_message['attachments'][0]['payload']['url']
        response = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type":
                    "generic",
                    "elements": [{
                        "title":
                        "Is this the right picture?",
                        "subtitle":
                        "Tap a button to answer.",
                        "image_url":
                        message,
                        "buttons": [{
                            "type": "postback",
                            "title": "Yes!",
                            "payload": "yes",
                        }, {
                            "type": "postback",
                            "title": "No!",
                            "payload": "no",
                        }],
                    }]
                }
            }
        }
        call_send_API(sender_psid, response)


# get post backs and handle them
def handle_postback(sender_psid, recieved_postback):
    payload = recieved_postback.payload
    if payload == 'yes':
        response = {'text': "thanks"}
    elif payload == 'no':
        response = {'text': "oops!! try sending another message"}
    call_send_API(sender_psid, response)
    pass


# query the send api and return a reply
def call_send_API(sender_psid, response):
    message_body = {'id': sender_psid, 'message': response}
    print(message_body)
    bot = Bot(ACCESS_TOKEN)
    bot.send_message(sender_psid, response)


if __name__ == '__main__':
    app.run(debug=True)
