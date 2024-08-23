# Calendis Availability Checker

This project is an automated tool that checks for available slots on the Calendis sports facility booking system in Cluj-Napoca, specifically for football (soccer) bookings. When available slots are found, it sends a notification to a specified Discord channel.

## Features

- Automatically checks for available football slots on Calendis
- Focuses on 20:00 and 21:00 time slots
- Runs every 6 hours via GitHub Actions
- Sends notifications to a Discord channel when slots are available

## Requirements

- Python 3.10
- Firefox browser
- GeckoDriver
- Discord bot token and channel ID
- Calendis account credentials

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/calendis-availability-checker.git
   cd calendis-availability-checker
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up the following secrets in your GitHub repository:
   - `DISCORD_TOKEN`: Your Discord bot token
   - `DISCORD_CHANNEL_ID`: The ID of the Discord channel for notifications
   - `CALENDIS_EMAIL`: Your Calendis account email
   - `CALENDIS_PASSWORD`: Your Calendis account password

4. The GitHub Actions workflow will automatically set up Firefox and GeckoDriver.

## Usage

The checker runs automatically every 6 hours via GitHub Actions. You can also manually trigger the workflow from the Actions tab in your GitHub repository.

To run the script locally:

1. Set up the required environment variables:
   ```
   export DISCORD_TOKEN=your_discord_token
   export DISCORD_CHANNEL_ID=your_channel_id
   export EMAIL=your_calendis_email
   export ACC_PASSWORD=your_calendis_password
   export GECKODRIVER_PATH=/path/to/geckodriver
   ```

2. Run the script:
   ```
   python main.py
   ```

## How It Works

1. The script logs into Calendis using the provided credentials.
2. It navigates to the football booking page for Baza Sportiva Gheorgheni.
3. It checks for available slots at 20:00 and 21:00 for the next 14 days.
4. If slots are available, it sends a message to the specified Discord channel.

## Troubleshooting

- If you encounter issues with GeckoDriver, make sure it's in your system PATH or set the `GECKODRIVER_PATH` environment variable.
- Check the GitHub Actions logs for any error messages if the automated runs fail.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
