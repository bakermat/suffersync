import configparser
import requests
import json
import re
import os
import sys
from datetime import datetime
from base64 import b64encode


def write_configfile(config, filename):
    text = r"""
[DEFAULT]
# Change this to 1 if you want to upload yoga workouts to intervals.icu
UPLOAD_YOGA_WORKOUTS = 0
# Change this to 1 if you want to upload past SYSTM workouts to intervals.icu
UPLOAD_PAST_WORKOUTS = 0

[WAHOO]
# Your Wahoo SYSTM credentials
SYSTM_USERNAME = your_systm_username
SYSTM_PASSWORD = your_systm_password

# Start and end date of workouts you want to send to intervals.icu.
# Use YYYY-MM-DD format
START_DATE = 2021-11-01
END_DATE = 2021-12-31

[INTERVALS.ICU]
# Your intervals.icu API ID and API key
INTERVALS_ICU_ID = i00000
INTERVALS_ICU_APIKEY = xxxxxxxxxxxxx
"""
    with open(filename, 'w') as configfile:
        configfile.write(text)
    print(f'Created {filename}. Add your user details to that file and run suffersync again.')
    sys.exit(0)

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
        print(f'Invalid Wahoo SYSTM username or password. Please check your settings and try again.')
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


def upload_to_intervals_icu(date, filename, contents, userid, api_key):
    url = f'https://intervals.icu/api/v1/athlete/{userid}/events'

    payload = json.dumps({
        "category": "WORKOUT",
        "start_date_local": date,
        "type": "Ride",
        "filename": filename,
        "file_contents": contents
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
    # Read config file
    CONFIGFILE = 'suffersync.cfg'
    config = configparser.ConfigParser()

    config_exists = os.path.exists(CONFIGFILE)
    if config_exists:
        try:
            config.read(CONFIGFILE)
            UPLOAD_YOGA_WORKOUTS = int(config['DEFAULT']['UPLOAD_YOGA_WORKOUTS'])
            UPLOAD_PAST_WORKOUTS = int(config['DEFAULT']['UPLOAD_PAST_WORKOUTS'])
            SYSTM_USERNAME = config['WAHOO']['SYSTM_USERNAME']
            SYSTM_PASSWORD = config['WAHOO']['SYSTM_PASSWORD']
            START_DATE = config['WAHOO']['START_DATE']
            END_DATE = config['WAHOO']['END_DATE']
            INTERVALS_ICU_ID = config['INTERVALS.ICU']['INTERVALS_ICU_ID']
            INTERVALS_ICU_APIKEY = config['INTERVALS.ICU']['INTERVALS_ICU_APIKEY']
        except KeyError:
            print(f'Could not read {CONFIGFILE}. Please check again.')
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
            workout_name = re.sub("[:]", "", workout_name)
            workout_name = re.sub("[ ,./]", "_", workout_name)
            filename = f'{dt_workout_date_short}_{workout_name}'

            try:
                workout_id = item['prospects'][0]['workoutId']
            except Exception as err:
                print(f'Error: {err}')

            # Get specific workout
            workout_detail = get_systm_workout(SYSTM_URL, systm_token, workout_id)

            # Create .zwo files with workout details
            filename_zwo = f'./zwo/{filename}.zwo'
            os.makedirs(os.path.dirname(filename_zwo), exist_ok=True)

            try:
                # Workout details are not clean JSON, so use clean_workout() before loading as JSON
                workout_detail = clean_workout(workout_detail)
                workout_json = json.loads(workout_detail)
                sport = workout_json['data']['workouts'][0]['sport']

                # Skip yoga workouts if UPLOAD_YOGA_WORKOUTS = 0
                if sport == 'Yoga' and not UPLOAD_YOGA_WORKOUTS:
                    continue

                if sport == 'Cycling':
                    sporttype = 'bike'
                elif sport == 'Yoga':
                    sporttype = 'yoga'
                elif sport == 'Running':
                    sporttype = 'run'

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
    <description></description>
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
                date = filename_zwo[6:16]
                file_date = f'{date}T00:00:00'
                date = datetime.strptime(date, "%Y-%m-%d")
                intervals_filename = f'{filename_zwo[17:]}'
                file_contents = zwo_file.read()

                if date > today or UPLOAD_PAST_WORKOUTS:
                    response = upload_to_intervals_icu(file_date, intervals_filename, file_contents, INTERVALS_ICU_ID, INTERVALS_ICU_APIKEY)
                    if response.status_code == 200:
                        print(f'Uploaded {intervals_filename}')

                zwo_file.close()
            except Exception as err:
                print(f'Something went wrong with {intervals_filename}: {err}')


if __name__ == "__main__":
    main()
