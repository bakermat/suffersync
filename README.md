# SufferSync

SufferSync gets upcoming workouts from your Wahoo SYSTM training plan and syncs these with [intervals.icu](https://intervals.icu).

## Getting Started
- Make sure you have Python 3 with the `requests` and `dateutil` packages. You can install these as follows:
    - `pip install requests python-dateutil`
- Get your Wahoo SYSTM HTTP Authorization token:
    - Open your Developer Tools in the Chrome browser, go to https://systm.wahoofitness.com and login. 
    - Click on the Network tab in the Developer Tools, find a `graphql` entry and click on the Headers tab.
    - Find an `authorization: Bearer ...` field, copy **only** the (really long) string after `Bearer`.
    - For example, it might be `authorization: Bearer e9aFylZcMg0IiemLad...` (and more), copy the `e9a` part till the end, don't include `authorization: Bearer`.
- Get your [intervals.icu](https://intervals.icu) API key on your [account](https://intervals.icu/settings) page.
- Update the Python script with your Wahoo SYSTM token, the dates that you want to get the activities for and your intervals.icu athlete id & API key.
- Run the app with `python3 ./suffersync.py`

## Caveats
A small minority of rides might not be a 100% match, which could be due to level mode or workout information missing. Examples are _Half Monty_, _The Stig_ and _ProRides: Strade Bianchi 1_ ride from my quick observation.

## Disclaimer
This website is in no way affiliated with either Wahoo SYSTM or https://intervals.icu. It was developed for personal use and is not supported. I welcome pull requests if you want to contribute.

## License
MIT
