"""Fetch and print a random dad joke from icanhazdadjoke.com."""

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main():
    request = Request(
        "https://icanhazdadjoke.com/",
        headers={
            "Accept": "application/json",
            "User-Agent": "DadJokeScript (Python urllib)",
        },
    )
    try:
        with urlopen(request, timeout=10) as response:
            data = json.load(response)
        joke = data.get("joke")
        if not isinstance(joke, str) or not joke.strip():
            raise ValueError("The API did not return a joke.")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        print(f"Could not fetch a dad joke: {exc}", file=sys.stderr)
        return 1

    print(joke)
    return joke


if __name__ == "__main__":
    main()
