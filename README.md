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

## Changes in v1.4.1
- Improved handling of workouts without any data.
- Improved handling of passwords that contain special characters.

## Changes in v1.4.0
- Existing workouts in intervals.icu will now be overwritten when they have the same name to avoid duplicate uploads.
- Special characters like '.' or ':' will now show up correctly in intervals.icu. If you upgraded from an older release, you might see a few duplicates for workouts that have a '.' or '/' in them, you will have to manually remove the ones without these characters from intervals.icu.
- Added  option to delete planned events in intervals.icu using `suffersync -d` or `suffersync --delete`. It will delete all events for the date range specified in `suffersync.cfg`.
- If you're training for an event, the event at the end of your plan will be included in the intervals.icu calendar as a note.

## Changes in v1.3.0
- Introduced the option to include swim, run and strength training for uploading to intervals.icu. By default they're all disabled.
- Introduced the option to add the Wahoo SYSTM description to the intervals.icu workout. It's pretty verbose so this is also optional and disabled by default.
- When you upgrade from an older version you won't see these options in the config file, they don't get added automatically. You can either add these manually or the easier option is probably to add these by removing the config file and recreating it when using the `suffersync` app as they will show up then.

## Disclaimer
This website is in no way affiliated with either Wahoo SYSTM or https://intervals.icu. It was developed for personal use and is not supported. I welcome pull requests if you want to contribute.