## Overview
SufferSync syncs workouts from your Wahoo SYSTM training plan with [intervals.icu](https://intervals.icu).

## Getting Started
- Install this app: `pip install suffersync`.
- Get your intervals.icu API key on your [account page](https://intervals.icu/settings).
- Run the app once using `suffersync` in a terminal, it'll create a `suffersync.cfg` file in your current directory.
- Open `suffersync.cfg` and add your configuration:
    - By default only future ride and run workouts are included. Yoga and strength workouts are ignored, change the respective values to suit your needs.
    - Add your Wahoo SYSTM username & password.
    - The start & end dates that you want to get the activities for.
    - Your intervals.icu athlete id & API key.
- Run the app with `suffersync` or `python -m suffersync`.

## Upgrade to v1.3.0 from an older version
- Version 1.3.0 introduced the option to include or exclude uploading runs and strength training. By default runs are uploaded to intervals.icu, strength workouts are excluded. If you're upgrading from an older version and you want to change these settings you will have to add `UPLOAD_RUN_WORKOUTS = 0`and `UPLOAD_STRENGTH_WORKOUTS = 1` to `sufferfest.cfg` manually to change the default behaviour. Alternatively you can remove `sufferfest.cfg` and a new one will be created the next time you run `suffersync`.

## Disclaimer
This website is in no way affiliated with either Wahoo SYSTM or https://intervals.icu. It was developed for personal use and is not supported. I welcome pull requests if you want to contribute.