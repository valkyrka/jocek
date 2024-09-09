# Jocek
## _The accountant you didn't know you need_

Jocek is a friendly Discord bot acting as an accountant doing a couple of things:

- 👷‍♂️ responds to ping requests for users that use the `!ping` commmand
- 🧌 wishes a particular user an easy shift before starting work Sunday -> Thursday
- 🛤️ tracks status changes and posts it in a particular channel (statuses are mainly user starting/stopping playing games)
- ✨ posts stats about user's gameplays every night at 21.00 UTC
- 🐩 reacts to the emoji of a dog from a certain user and posts a message when the emoji reaction is added
- 🦸‍♂️ responds w/ the contents of of a file if you ask it stuff like flow, cloudstick or DNS
- ⏳ posts info about when a tagged user was last seen online

## Technologies used

- Python (works on Python 3.9+)
- Discord.py
- Tabulate
- Linux

## Installation & running

Jocek requires [Python](https://www.python.org/downloads/) 3.9+ to run.

Install the dependencies and start it in a screen session.

```sh
pip3 install -r requirements.txt -t .
screen -S jocek
./jocek.sh
```