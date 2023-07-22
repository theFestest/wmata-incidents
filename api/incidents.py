
import datetime
import os
import requests
import vercel_kv
from datetime import datetime
from atproto import Client
from http.server import BaseHTTPRequestHandler

WMATA_API_KEY = os.getenv("api_key")
BOT_HANDLE = os.getenv("bot_handle")
BOT_APP_PASSWORD = os.getenv("bot_app_password")

# Vercel KV related args for state keeping.
VERCEL_KV_URL = os.getenv("VERCEL_KV_URL")
VERCEL_KV_REST_API_URL = os.getenv("VERCEL_KV_REST_API_URL")
VERCEL_KV_REST_API_TOKEN = os.getenv("VERCEL_KV_REST_API_TOKEN")
VERCEL_KV_REST_API_READ_ONLY_TOKEN = os.getenv("VERCEL_KV_REST_API_READ_ONLY_TOKEN")

at_client = None
kv_client = None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Hello, world!'.encode('utf-8'))
        return


def send_post(text: str):
    """Send post with the given text content
    return post_ref of generated post
    """
    print("Sending post with text: ", text)
    if at_client is None:
        at_login()

    try:
        at_client.send_post(text=text)
    except Exception as ex:
        print("Failed to send post. Got error: ", str(ex))
        return False
    return True


def at_login():
    """Login with the atproto client
    """
    global at_client
    at_client = Client()
    profile = at_client.login(BOT_HANDLE, BOT_APP_PASSWORD)
    print("Logged in as: ", profile.displayName)


def is_newer(update_time: str, last_posted: str) -> bool:
    """Determine if update_time is more recent than the retrieved"""
    if last_posted is None or last_posted == "":
        return True
    update_time = datetime.fromisoformat(update_time)
    last_posted = datetime.fromisoformat(last_posted)
    return update_time > last_posted


def get_train_incidents():
    """Query WMATA for train incidents
    """
    pass


def get_bus_incidents():
    """Query WMATA for bus incidents
    """
    pass


def get_elevator_incidents() -> requests.Response:
    """Query WMATA for elevator incidents
    """
    pass


def login_kv():
    global kv_client
    kv_client = vercel_kv.KV(
        kv_config=vercel_kv.KVConfig(
            url=VERCEL_KV_URL,
            rest_api_url=VERCEL_KV_REST_API_URL,
            rest_api_token=VERCEL_KV_REST_API_TOKEN,
            rest_api_read_only_token=VERCEL_KV_REST_API_READ_ONLY_TOKEN
        )
    )


def find_new_incidents(incident_list):
    """Collect new / updated incidents based on kv records
    """
    new_incidents = []
    if kv_client is None:
        login_kv()

    if kv_client.has_auth():
        for incident in incident_list:
            last_posted_update = kv_client.get(incident["IncidentID"])
            # TODO: what happens if the key has never been used? returns '{"result":null}' i.e. None?
            if is_newer(incident["DateUpdated"], last_posted_update):
                new_incidents.append(incident)
    else:
        print("Unable to access kv store to check incident history! Skipping to avoid post spam!")
    return new_incidents


def update_last_posted(incident_id, date_updated):
    """Store last updated time for this incident id in kv.
    """
    if kv_client is None:
        login_kv()

    if kv_client.has_auth():
        kv_client.set(incident_id, date_updated)
    else:
        print("Unable to access kv store to check incident history! Warning may post spam!")


def make_train_incident_text(incident_dict: dict):
    """Generate formatted post body for train incidents
    Example response:
    {
        'Incidents': [{
            'IncidentID': '7CC6238D-0BA9-4CED-B6B4-E769DEB07E67',
            'Description': 'Expect residual delays to Vienna, Ashburn & Franconia due to an earlier switch problem at Smithsonian.',
            // 'StartLocationFullName': None,
            // 'EndLocationFullName': None,
            // 'PassengerDelay': 0.0,
            // 'DelaySeverity': None,
            'IncidentType': 'Delay',
            // 'EmergencyText': None,
            'LinesAffected': 'BL; OR; SV;',
            'DateUpdated': '2023-07-21T21:01:50'
        }]
    }
    """
    def line_format(line_string):
        lines = line_string.split(";")
        cleaned_lines = [line.strip() for line in lines if line.strip() != ""]
        return ", ".join(cleaned_lines)

    return f"""Train incident reported affecting the following lines: {line_format(incident_dict['LinesAffected'])}.

    {incident_dict['IncidentType']}: {incident_dict['Description']}

    Last updated: {datetime.fromisoformat(incident_dict['DateUpdated'])} (Eastern Time)."""


def make_bus_incident_text(incident_dict: dict):
    """Generate formatted post body for bus incidents
    Example response:
    {
        'BusIncidents': [{
            'IncidentID': '2973AF5D-F62B-416A-987C-7A5E597BDCDB',
            'IncidentType': 'Alert',
            'RoutesAffected': ['P12'],
            'Description': 'Some P12 trips may be delayed due to operator availability. Check where your bus is at https://buseta.wmata.com/#P12',
            'DateUpdated': '2023-07-21T21:06:59'
        }]
    }
    """
    return f"""Bus incident reported affecting the following routes: {','.join(incident_dict['RoutesAffected'])}.

    {incident_dict['IncidentType']}: {incident_dict['Description']}

    Last updated: {datetime.fromisoformat(incident_dict['DateUpdated'])} (Eastern Time)."""


def make_elevator_incident_text(incident_dict: dict):
    """Generate formatted post body for elevator incidents
    Example response:
    {
        'ElevatorIncidents': [{
            'UnitName': 'A01W02',
            'UnitType': 'ESCALATOR',
            // 'UnitStatus': None,
            'StationCode': 'A01',
            'StationName': 'Metro Center, G and 13th St Entrance',
            'LocationDescription': 'Escalator between street and mezzanine',
            // 'SymptomCode': None,
            // 'TimeOutOfService': '0509',
            'SymptomDescription': 'Modernization',
            // 'DisplayOrder': 0.0,
            'DateOutOfServ': '2023-05-05T05:09:00',
            'DateUpdated': '2023-06-27T09:13:17',
            'EstimatedReturnToService': '2023-09-04T23:59:59'
        }]
    }
    """
    pass  # TODO: since there are no incident ids, these need to be identified by Unit name?


def main():
    print(f"Cron has been invoked at {datetime.now()}")

    # Step 0: generate auth header
    wmata_header = {"api_key": WMATA_API_KEY}

    # Step 1: Check incidents
    train_resp = requests.get(url="https://api.wmata.com/Incidents.svc/json/Incidents", headers=wmata_header)
    bus_resp = requests.get(url="https://api.wmata.com/Incidents.svc/json/BusIncidents", headers=wmata_header)
    # elevator_resp = requests.get(url="https://api.wmata.com/Incidents.svc/json/ElevatorIncidents", headers=wmata_header)

    print("Got train incident response: ", train_resp.json())
    print("Got bus incident response: ", bus_resp.json())
    # print("Got elevator incident response: ", elevator_resp.json())

    # Step 2: Collect relevant incidents (check kv for past incident reports)
    new_train = find_new_incidents(train_resp.json()['Incidents'])
    new_bus = find_new_incidents(bus_resp.json()['BusIncidents'])
    # new_elevator = find_new_incidents(elevator_resp.json()['ElevatorIncidents'])

    print(f"Got {len(new_train)} new train incidents")
    print(f"Got {len(new_bus)} new bus incidents")
    # print(f"Got {len(new_elevator)} elevator incidents")

    # Step 3: Generate posts to send (post_text, incident_id, date_updated)
    to_send: list[(str, str, str)] = []
    to_send.extend(
        [(make_train_incident_text(incident), incident['IncidentID'], incident['DateUpdated']) for incident in new_train]
        )
    to_send.extend(
        [(make_bus_incident_text(incident), incident['IncidentID'], incident['DateUpdated']) for incident in new_bus]
        )
    # to_send.extend(
    #     [make_elevator_incident_text(incident) for incident in new_elevator]
    #     )

    # Step 4: Send posts and update last post time in kv.
    posts = 0
    for post_tuple in to_send:
        breakpoint()
        if send_post(post_tuple[0]):
            # Only update kv with posts that successfully sent in case of send error
            update_last_posted(post_tuple[1], post_tuple[2])
            posts += 1
        else:
            print("Post failed! Moving on...")

    print(f"Sent {len(posts)} incident posts. Exiting...")


if __name__ == "__main__":
    main()
