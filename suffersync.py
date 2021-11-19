import requests
import json
import re
import os
import sys
from datetime import datetime
from dateutil import tz
from base64 import b64encode

########################################################################################################
# Change these to your own Wahoo SYSTM credentials & intervals.icu                                     #
# Setup the dates you want to get the workouts for, only future workouts will be sent to intervals.icu #
########################################################################################################
SYSTM_TOKEN = 'xxx'
INTERVALS_ICU_ID = "i00000"
INTERVALS_ICU_APIKEY = "xxx"
START_DATE = "2021-11-01T00:00:00.000Z"
END_DATE = "2021-12-31T23:59:59.999Z"

# Don't change anything below this line
def call_api(url, headers, payload):
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
    except Exception as err:
        raise(err)
    return response


def clean_workout(workout):
    # Remove the details section, too many string errors.
    regex = r"(\"details.*?)(?=\"l)"
    workout = re.sub(regex, "", workout, 0, re.MULTILINE)
    # Remove '\\\"' in the trigger section
    workout = workout.replace("\\\\\\\"", "")
    # Remove the '\\', mostly seen in the trigger section
    workout = workout.replace("\\", "")
    # Make sure that the 'triggers' section is JSON compliant, remove the " at the start and end.
    workout = workout.replace('"triggers":"', '"triggers":')
    workout = workout.replace('","featuredRaces"', ',"featuredRaces"')
    return workout


def main():
    SYSTM_URL = "https://api.thesufferfest.com/graphql"

    payload = json.dumps({
        "operationName": "GetUserPlansRange",
        "variables": {
            "startDate": f'{START_DATE}',
            "endDate": f'{END_DATE}',
            "queryParams": {
                "limit": 1000
            }
        },
        "query": "query GetUserPlansRange($startDate: Date, $endDate: Date, $queryParams: QueryParams) { userPlan(startDate: $startDate, endDate: $endDate, queryParams: $queryParams) { ...UserPlanItem_fragment __typename }}fragment UserPlanItem_fragment on UserPlanItem { day plannedDate rank agendaId status type appliedTimeZone completionData { name date activityId durationSeconds style deleted __typename } prospects { type name compatibility description style intensity { master nm ac map ftp __typename } trainerSetting { mode level __typename } plannedDuration durationType metrics { ratings { nm ac map ftp __typename } __typename } contentId workoutId notes fourDPWorkoutGraph { time value type __typename } __typename } plan { id name color deleted durationDays startDate endDate addons level subcategory weakness description category grouping option uniqueToPlan type progression planDescription volume __typename } __typename}"
    })

    systm_headers = {
        'Authorization': f'Bearer {SYSTM_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Get workouts fro Wahoo SYSTM plan
    workouts = call_api(SYSTM_URL, systm_headers, payload).json()

    # Even with errors, response.status_code = 200 so catching errors this way.
    if 'errors' in workouts:
        print(f'Wahoo SYSTM Error: {workouts["errors"][0]["message"]}')
        sys.exit(1)

    workouts = workouts['data']['userPlan']
    workouts_list = []

    # For each item, make sure there's a "plannedDate" field to avoid bogus entries.
    for item in workouts:
        if item['plannedDate']:
            # Get plannedDate, convert to UTC DateTime and then to local timezone
            planned_date = item['plannedDate']
            dt_planned_date = datetime.strptime(planned_date, "%Y-%m-%dT%H:%M:%S.%fZ")
            timezone = tz.gettz(item['appliedTimeZone'])
            dt_workout_date_utc = dt_planned_date.replace(tzinfo=tz.gettz('UTC'))
            dt_workout_date_local = dt_workout_date_utc.astimezone(timezone)
            dt_workout_date_short = dt_workout_date_local.strftime("%Y-%m-%d")

            # Get workout name and remove invalid characters to avoid filename issues.
            workout_name = item['prospects'][0]['name']
            workout_name = re.sub("[:]", "", workout_name)
            workout_name = re.sub("[ ,./]", "_", workout_name)
            filename = f'{dt_workout_date_short}_{workout_name}'

            try:
                workout_id = item['prospects'][0]['workoutId']
                workout_details = {"workout_id": workout_id, "filename": filename}
                workouts_list.append(workout_details)
            except Exception as err:
                print(f'Error: {err}')

            filename_zwo = f'./zwo/{filename}.zwo'

            payload = json.dumps({
                "operationName": "GetWorkouts",
                "variables": {
                    "id": workout_id
                },
                "query": "query GetWorkouts($id: ID) {workouts(id: $id) { id sortOrder sport stampImage bannerImage bestFor equipment { name description thumbnail __typename } details shortDescription level durationSeconds name triggers featuredRaces { name thumbnail darkBackgroundThumbnail __typename } metrics { intensityFactor tss ratings { nm ac map ftp __typename } __typename } brand nonAppWorkout notes tags imperatives { userSettings { birthday gender weight __typename } __typename } __typename}}"
            })

            workout_detail = call_api(SYSTM_URL, systm_headers, payload).text

            try:
                # Workout details is not clean JSON, so use clean_workout() before loading as JSON
                workout_detail = clean_workout(workout_detail)
                workout_json = json.loads(workout_detail)
                sport = workout_json['data']['workouts'][0]['sport']

                # Skip yoga workouts
                if sport == 'Yoga':
                    continue

                workout_json = workout_json['data']['workouts'][0]['triggers']

                interval_name = ''
                os.makedirs(os.path.dirname(filename_zwo), exist_ok=True)
                f = open(filename_zwo, "a")
                if not workout_json:
                    f.write('No workout data found.')
                    f.close()
                else:
                    text = f"""
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workout_file>
    <author></author>
    <name>{interval_name}</name>
    <description></description>
    <sportType>bike</sportType>
    <tags/>
    <workout>"""
                    f.write(text)

                    for interval in range(len(workout_json)):
                        interval_name_counter = 0
                        for tracks in range(len(workout_json[interval]['tracks'])):
                            if 'name' in workout_json[interval]:
                                interval_name = workout_json[interval]['name']
                            if interval_name_counter == 0:
                                interval_name_counter += 1
                            for item in workout_json[interval]['tracks'][tracks]['objects']:
                                seconds = int(item['size'] / 1000)
                                if 'ftp' in item['parameters']:
                                    ftp = item['parameters']['ftp']['value']
                                    if 'rpm' in item['parameters']:
                                        rpm = item['parameters']['rpm']['value']
                                        text = f'\n\t\t<SteadyState show_avg="1" Cadence="{rpm}" Power="{ftp}" Duration="{seconds}"/>'
                                    else:
                                        text = f'\n\t\t<SteadyState show_avg="1" Power="{ftp}" Duration="{seconds}"/>'
                                    f.write(text)
                    text = r"""
    </workout>
</workout_file>"""
                    f.write(text)

            except Exception as err:
                print(f'{err}')

            f.close()

            try:
                today = datetime.today()
                zwo_file = open(filename_zwo, 'r')
                date = filename_zwo[6:16]
                file_date = f'{date}T00:00:00'
                date = datetime.strptime(date, "%Y-%m-%d")
                intervals_filename = f'{filename_zwo[17:]}'
                file_contents = zwo_file.read()

                if date > today:
                    intervals_icu_url = f'https://intervals.icu/api/v1/athlete/{INTERVALS_ICU_ID}/events'

                    intervals_icu_payload = json.dumps({
                        "category": "WORKOUT",
                        "start_date_local": file_date,
                        "type": "Ride",
                        "filename": intervals_filename,
                        "file_contents": file_contents
                    })

                    interval_icu_token = b64encode(f'API_KEY:{INTERVALS_ICU_APIKEY}'.encode()).decode()
                    interval_icu_headers = {
                        'Authorization': f'Basic {interval_icu_token}',
                        'Content-Type': 'text/plain'
                    }

                    call_api(intervals_icu_url, interval_icu_headers, intervals_icu_payload)
                    print(f'Uploaded {intervals_filename}')

                zwo_file.close()
            except Exception as err:
                print(f'Something went wrong with {intervals_filename}: {err}')


if __name__ == "__main__":
    main()
