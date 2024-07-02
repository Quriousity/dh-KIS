import requests


# Discord Webhook
def SendMessage(message, discord):
    requests.post(d, {'content': message})