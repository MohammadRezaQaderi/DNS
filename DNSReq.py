import os
import requests

def get_secret_message():
    url = os.environ["www.google.com"]
    response = requests.get(url)
    print(f"The secret message is: {response.text}")

if __name__ == "__main__":
    get_secret_message()