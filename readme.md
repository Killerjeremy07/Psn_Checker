# Discord PSN Bot

## Setup

- Go to the Discord Developer Portal, create a new bot, and enable every privileged gateway intents.
- Obtain your Twitch app ID and app secret:
    1. Go to the Twitch Developer Console (https://dev.twitch.tv/console/apps)
    2. Create a new application or select an existing one (Use `https://localhost` as redirect URL)
    3. Note down the Client ID and Client Secret
- Open a terminal inside the folder of the project.
- Install the required libraries by typing in:
    ```
    pip install -r requirements.txt
    ```
- Open the `config.py` file and change your PSN API token, your Twitch credentials (Client ID and Client Secret), and the token of the Discord bot in the `Secret` class.
- Start up the main file by typing `python main.py` inside the terminal.