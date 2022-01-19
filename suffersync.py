import configparser
import requests
import json
import re
import os
import sys
from datetime import datetime
from base64 import b64encode
from xml.sax.saxutils import escape as escape_xml


def write_configfile(config, filename):
    text = r"""
[DEFAULT]
# Change these to 1 if you want to upload the respective workouts to intervals.icu
UPLOAD_RUN_WORKOUTS = 0
UPLOAD_SWIM_WORKOUTS = 0
UPLOAD_STRENGTH_WORKOUTS = 0
UPLOAD_YOGA_WORKOUTS = 0
# Change this to 1 if you want to upload past SYSTM workouts to intervals.icu
UPLOAD_PAST_WORKOUTS = 0
UPLOAD_DESCRIPTION = 0

[WAHOO]
# Your Wahoo SYSTM credentials
SYSTM_USERNAME = your_systm_username
SYSTM_PASSWORD = your_systm_password

# Start and end date of workouts you want to send to intervals.icu.
# Use YYYY-MM-DD format
START_DATE = 2022-01-01
END_DATE = 2022-12-31

[INTERVALS.ICU]
# Your intervals.icu API ID and API key
INTERVALS_ICU_ID = i00000
INTERVALS_ICU_APIKEY = xxxxxxxxxxxxx
"""
    with open(filename, 'w') as configfile:
        configfile.write(text)
    print(f'Created {filename}. Add your user details to that file and run suffersync again.')
    sys.exit(0)


def get_intervals_sport(sport):
    if sport == "Cycling":
        return "Ride"
    elif sport == "Running":
        return "Run"
    elif sport == "Yoga":
        return "Yoga"
    elif sport == "Strength":
        return "WeightTraining"
    elif sport == "Swimming":
        return "Swim"


def get_systm_token(url, username, password):
    payload = json.dumps({
        "operationName": "Login",
        "variables": {
            "appInformation": {
                "platform": "web",
                "version": "7.12.0-web.2141",
                "installId": "F215B34567B35AC815329A53A2B696E5"
            },
            "username": username,
            "password": password
        },
        "query": "mutation Login($appInformation: AppInformation!, $username: String!, $password: String!) { loginUser(appInformation: $appInformation, username: $username, password: $password) { status message user { ...User_fragment __typename } token failureId __typename }}fragment User_fragment on User { id fullName firstName lastName email gender birthday weightKg heightCm createdAt metric emailSharingOn legacyThresholdPower wahooId wheelSize { name id __typename } updatedAt profiles { riderProfile { ...UserProfile_fragment __typename } __typename } connectedServices { name __typename } timeZone onboardingProgress { complete completedSteps __typename } subscription { validUntil trialAvailable __typename } avatar { url original { url __typename } square200x200 { url __typename } square256x256 { url __typename } thumb { url __typename } __typename } onboardingComplete createdWithAppInformation { version platform __typename } __typename}fragment UserProfile_fragment on UserProfile { nm ac map ftp lthr cadenceThreshold riderTypeInfo { name icon iconSmall systmIcon description __typename } riderWeaknessInfo { name __typename } recommended { nm { value activity __typename } ac { value activity __typename } map { value activity __typename } ftp { value activity __typename } __typename } __typename}"
    })

    headers = {'Content-Type': 'application/json'}

    response = call_api(url, headers, payload)
    if 'login.badUserOrPassword' in response.text:
        print('Invalid Wahoo SYSTM username or password. Please check your settings and try again.')
        sys.exit(1)
    response_json = response.json()
    token = response_json['data']['loginUser']['token']
    rider_profile = response_json['data']['loginUser']['user']['profiles']['riderProfile']
    get_systm_profile(rider_profile)
    return token


def get_systm_profile(profile):
    # Get user's 4DP profile and set as global variables
    global rider_ac, rider_nm, rider_map, rider_ftp
    rider_ac = profile['ac']
    rider_nm = profile['nm']
    rider_map = profile['map']
    rider_ftp = profile['ftp']


def get_systm_workouts(url, token, start_date, end_date):
    payload = json.dumps({
        "operationName": "GetUserPlansRange",
        "variables": {
            "startDate": f"{start_date}T00:00:00.000Z",
            "endDate": f"{end_date}T23:59:59.999Z",
            "queryParams": {
                "limit": 1000
            }
        },
        "query": "query GetUserPlansRange($startDate: Date, $endDate: Date, $queryParams: QueryParams) { userPlan(startDate: $startDate, endDate: $endDate, queryParams: $queryParams) { ...UserPlanItem_fragment __typename }}fragment UserPlanItem_fragment on UserPlanItem { day plannedDate rank agendaId status type appliedTimeZone completionData { name date activityId durationSeconds style deleted __typename } prospects { type name compatibility description style intensity { master nm ac map ftp __typename } trainerSetting { mode level __typename } plannedDuration durationType metrics { ratings { nm ac map ftp __typename } __typename } contentId workoutId notes fourDPWorkoutGraph { time value type __typename } __typename } plan { id name color deleted durationDays startDate endDate addons level subcategory weakness description category grouping option uniqueToPlan type progression planDescription volume __typename } __typename}"
    })

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Get workouts from Wahoo SYSTM plan
    response = call_api(url, headers, payload).json()
    return response


def get_systm_workout(url, token, workout_id):
    payload = json.dumps({
        "operationName": "GetWorkouts",
        "variables": {
            "id": workout_id
        },
        "query": "query GetWorkouts($id: ID) {workouts(id: $id) { id sortOrder sport stampImage bannerImage bestFor equipment { name description thumbnail __typename } details shortDescription level durationSeconds name triggers featuredRaces { name thumbnail darkBackgroundThumbnail __typename } metrics { intensityFactor tss ratings { nm ac map ftp __typename } __typename } brand nonAppWorkout notes tags imperatives { userSettings { birthday gender weight __typename } __typename } __typename}}"
    })

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    response = call_api(url, headers, payload).text
    return response


def upload_to_intervals_icu(date, name, sport, userid, api_key, contents=None, moving_time=None, description=None):
    url = f'https://intervals.icu/api/v1/athlete/{userid}/events'

    if sport == "Ride":
        payload = json.dumps({
            "category": "WORKOUT",
            "start_date_local": date,
            "type": sport,
            "filename": name,
            "file_contents": contents
        })

    else:
        payload = json.dumps({
            "start_date_local": date,
            "description": description,
            "category": "WORKOUT",
            "name": name,
            "type": sport,
            "moving_time": moving_time
        })

    token = b64encode(f'API_KEY:{api_key}'.encode()).decode()
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': 'text/plain'
    }

    response = call_api(url, headers, payload)
    return response


def call_api(url, headers, payload):
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
    except Exception as err:
        raise(err)
    return response


def clean_workout(workout):
    workout_json = json.loads(workout)

    # workout ['data']['workouts'][0]['triggers'] appears to be a JSON string
    workout_json['data']['workouts'][0]['triggers'] = json.loads(workout_json['data']['workouts'][0]['triggers'])

    return workout_json


def main():
    # Read config file
    CONFIGFILE = 'suffersync.cfg'
    config = configparser.ConfigParser()

    config_exists = os.path.exists(CONFIGFILE)
    if config_exists:
        try:
            config.read(CONFIGFILE)
            UPLOAD_PAST_WORKOUTS = config.getint('DEFAULT', 'UPLOAD_PAST_WORKOUTS', fallback=0)
            UPLOAD_STRENGTH_WORKOUTS = config.getint('DEFAULT', 'UPLOAD_STRENGTH_WORKOUTS', fallback=0)
            UPLOAD_YOGA_WORKOUTS = config.getint('DEFAULT', 'UPLOAD_YOGA_WORKOUTS', fallback=0)
            UPLOAD_RUN_WORKOUTS = config.getint('DEFAULT', 'UPLOAD_RUN_WORKOUTS', fallback=0)
            UPLOAD_SWIM_WORKOUTS = config.getint('DEFAULT', 'UPLOAD_SWIM_WORKOUTS', fallback=0)
            UPLOAD_DESCRIPTION = config.getint('DEFAULT', 'UPLOAD_DESCRIPTION', fallback=0)
            SYSTM_USERNAME = config.get('WAHOO', 'SYSTM_USERNAME')
            SYSTM_PASSWORD = config.get('WAHOO', 'SYSTM_PASSWORD')
            START_DATE = config.get('WAHOO', 'START_DATE')
            END_DATE = config.get('WAHOO', 'END_DATE')
            INTERVALS_ICU_ID = config.get('INTERVALS.ICU', 'INTERVALS_ICU_ID')
            INTERVALS_ICU_APIKEY = config.get('INTERVALS.ICU', 'INTERVALS_ICU_APIKEY')
        except KeyError as err:
            print(f'No valid value found for key {err} in {CONFIGFILE}.')
            sys.exit(1)
    else:
        write_configfile(config, CONFIGFILE)

    SYSTM_URL = "https://api.thesufferfest.com/graphql"

    # Get Wahoo SYSTM auth token
    systm_token = get_systm_token(SYSTM_URL, SYSTM_USERNAME, SYSTM_PASSWORD)

    # Get Wahoo SYSTM workouts from training plan
    workouts = get_systm_workouts(SYSTM_URL, systm_token, START_DATE, END_DATE)

    # Even with errors, response.status_code comes back as 200 so catching errors this way.
    if 'errors' in workouts:
        print(f'Wahoo SYSTM Error: {workouts["errors"][0]["message"]}')
        sys.exit(1)

    workouts = workouts['data']['userPlan']

    # For each workout, make sure there's a "plannedDate" field to avoid bogus entries.
    for item in workouts:
        if item['plannedDate']:
            # Get plannedDate, convert to date_short for filenaming
            planned_date = item['plannedDate']
            dt_workout_date = datetime.strptime(planned_date, "%Y-%m-%dT%H:%M:%S.%fZ")
            dt_workout_date_short = dt_workout_date.strftime("%Y-%m-%d")

            # Get workout name and remove invalid characters to avoid filename issues.
            workout_name = item['prospects'][0]['name']
            workout_name_remove_colon = re.sub("[:]", "", workout_name)
            workout_name_underscores = re.sub("[ ,./]", "_", workout_name_remove_colon)
            filename = f'{dt_workout_date_short}_{workout_name_underscores}'

            try:
                workout_id = item['prospects'][0]['workoutId']
                workout_type = item['prospects'][0]['type']

                # get_intervals_sport will get the intervals.icu name for SYSTM's equivalent sport
                sport = get_intervals_sport(workout_type)

                # Skip workouts without detail and Mental Training workouts.
                if workout_id == '' or workout_type == 'MentalTraining':
                    continue
                # Non-ride workouts (run, strength, yoga) contain no information apart from duration and name, upload separately.
                if sport != 'Ride':
                    date = f'{dt_workout_date_short}T00:00:00'
                    description = item['prospects'][0]['description']
                    moving_time = round(float(item['prospects'][0]['plannedDuration']) * 3600)

                    if sport == 'Yoga' and not UPLOAD_YOGA_WORKOUTS:
                        continue
                    elif sport == 'WeightTraining' and not UPLOAD_STRENGTH_WORKOUTS:
                        continue
                    elif sport == 'Run' and not UPLOAD_RUN_WORKOUTS:
                        continue
                    elif sport == 'Swim' and not UPLOAD_SWIM_WORKOUTS:
                        continue
                    else:
                        response = upload_to_intervals_icu(date, workout_name, sport, INTERVALS_ICU_ID, INTERVALS_ICU_APIKEY, description=description, moving_time=moving_time)
                        if response.status_code == 200:
                            print(f'Uploaded {dt_workout_date_short}: {workout_name} ({sport})')
                        continue

            except Exception as err:
                print(f'Error: {err}')

            # Get specific workout
            workout_detail = get_systm_workout(SYSTM_URL, systm_token, workout_id)

            # Create .zwo files with workout details
            filename_zwo = f'./zwo/{filename}.zwo'
            os.makedirs(os.path.dirname(filename_zwo), exist_ok=True)

            try:
                # Workout details contain nested JSON, so use clean_workout() to handle this.
                workout_json = clean_workout(workout_detail)

                if sport == 'Ride':
                    sporttype = 'bike'

                # If UPLOAD_DESCRIPTION is set, change description of workout to Wahoo SYSTM's description.
                description = ''

                if UPLOAD_DESCRIPTION:
                    description = workout_json['data']['workouts'][0]['details']
                    description = escape_xml(description)

                # 'triggers' contains the FTP values for the workout
                workout_json = workout_json['data']['workouts'][0]['triggers']

                f = open(filename_zwo, "w")
                if not workout_json:
                    f.write('No workout data found.')
                    f.close()
                else:
                    text = f"""
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workout_file>
    <author></author>
    <name></name>
    <description>{description}</description>
    <sportType>{sporttype}</sportType>
    <tags/>
    <workout>"""
                    f.write(text)

                    for interval in range(len(workout_json)):
                        for tracks in range(len(workout_json[interval]['tracks'])):
                            for item in workout_json[interval]['tracks'][tracks]['objects']:
                                power = None
                                seconds = int(item['size'] / 1000)
                                if 'ftp' in item['parameters']:
                                    power = item['parameters']['ftp']['value']
                                # Not sure if required, in my data this always seems to be the same as ftp
                                if 'twentyMin' in item['parameters']:
                                    twentyMin = item['parameters']['twentyMin']['value']
                                    power = max(power, twentyMin)
                                # If map value exists, set ftp to the higher value of either map or ftp.
                                if 'map' in item['parameters']:
                                    map = item['parameters']['map']['value'] * round(rider_map / rider_ftp, 2)
                                    power = max(power, map)
                                if 'ac' in item['parameters']:
                                    ac = item['parameters']['ac']['value'] * round(rider_ac / rider_ftp, 2)
                                    power = max(power, ac)
                                if 'nm' in item['parameters']:
                                    nm = item['parameters']['nm']['value'] * round(rider_nm / rider_ftp, 2)
                                    power = max(power, nm)
                                if power:
                                    if 'rpm' in item['parameters']:
                                        rpm = item['parameters']['rpm']['value']
                                        text = f'\n\t\t<SteadyState show_avg="1" Cadence="{rpm}" Power="{power}" Duration="{seconds}"/>'
                                    else:
                                        text = f'\n\t\t<SteadyState show_avg="1" Power="{power}" Duration="{seconds}"/>'
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
                date_short = filename_zwo[6:16]
                file_date = f'{date_short}T00:00:00'
                date = datetime.strptime(date_short, "%Y-%m-%d")
                intervals_filename = f'{filename_zwo[17:]}'
                file_contents = zwo_file.read()

                if date >= today or UPLOAD_PAST_WORKOUTS:
                    response = upload_to_intervals_icu(file_date, intervals_filename, sport, INTERVALS_ICU_ID, INTERVALS_ICU_APIKEY, contents=file_contents)
                    if response.status_code == 200:
                        print(f'Uploaded {date_short}: {intervals_filename} ({sport})')

                zwo_file.close()
            except Exception as err:
                print(f'Something went wrong: {err}')


if __name__ == "__main__":
    main()
