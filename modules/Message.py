import requests


# Discord Webhook
def SendMessage(message, discord):
    for d in discord:
        requests.post(d, {'content': message})