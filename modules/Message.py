import requests


# Discord Webhook
def SendMessage(message, discord):
    requests.post(discord, {'content': message})