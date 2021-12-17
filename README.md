# SufferSync

SufferSync gets upcoming workouts from your Wahoo SYSTM training plan and syncs these with [intervals.icu](https://intervals.icu).

## Getting Started
- Make sure you have Python 3 with the `requests` and `dateutil` packages. You can install these as follows:
    - `pip install requests python-dateutil`
- Get your [intervals.icu](https://intervals.icu) API key on your [account](https://intervals.icu/settings) page.
- Update the Python script at the top:
    - Add your Wahoo SYSTM username & password.
    - The start & end dates that you want to get the activities for.
    - Your intervals.icu athlete id & API key.
    - By default only future workouts are included and yoga workouts are ignored, change the respective values if you want past workouts or yoga workouts to be synced.
- Run the app with `python3 ./suffersync.py`

## Disclaimer
This website is in no way affiliated with either Wahoo SYSTM or https://intervals.icu. It was developed for personal use and is not supported. I welcome pull requests if you want to contribute.

## License
MIT
