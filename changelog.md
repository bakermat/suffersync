## Changes in v1.4.3
- Fixed datetime and encoding issue (by @alexandermuehle)
- Fixed issue where distance mentioned in the description of a workout could cause an incorrect workout file.

## Changes in v1.4.2
- Corrected interval steps for MAP, AC and NM (by @knutpett).
- Replace Ride with VirtualRide for SYSTM activities.

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
