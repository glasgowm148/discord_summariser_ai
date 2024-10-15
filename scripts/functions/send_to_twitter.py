# send_to_twitter.py
import requests
from requests_oauthlib import OAuth1

def send_to_twitter(tweet):
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(
        os.getenv("TWITTER_CONSUMER_KEY"),
        os.getenv("TWITTER_CONSUMER_SECRET"),
        os.getenv("TWITTER_ACCESS_TOKEN"),
        os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    )
    payload = {"text": tweet}
    print("Sending tweet...")
    try:
        response = requests.post(url, auth=auth, json=payload)
        if response.status_code in (200, 201):
            print("Tweet sent successfully.")
        else:
            error_detail = response.json().get('detail') or response.json().get('errors', response.json())
            print(f"Error sending tweet: {error_detail}")
    except Exception as e:
        print(f"Exception while sending tweet: {e}")
