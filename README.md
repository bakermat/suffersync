## Overview
SufferSync syncs workouts from your Wahoo SYSTM training plan with [intervals.icu](https://intervals.icu).

## Getting Started
- Install this app: `pip install suffersync`.
- Get your intervals.icu API key on your [account page](https://intervals.icu/settings).
- Run the app once using `suffersync` in a terminal, it'll create a `suffersync.cfg` file in your current directory.
- Open `suffersync.cfg` and add your configuration:
    - By default only future ride workouts are included. Yoga, swim, run and strength workouts are ignored, change the respective values in the config file to suit your needs.
    - Add your Wahoo SYSTM username & password.
    - The start & end dates that you want to get the activities for.
    - Your intervals.icu athlete id & API key.
- Run the app with `suffersync` or `python -m suffersync`.
- You can delete events using the range in the config file with `suffersync -d`.

## Disclaimer
This website is in no way affiliated with either Wahoo SYSTM or https://intervals.icu. It was developed for personal use and is not supported. I welcome pull requests if you want to contribute.