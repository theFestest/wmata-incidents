import datetime
import os
from typing import Union, Optional
from textwrap import dedent

import requests
# from .vercel_kv import KV, KVConfig
from datetime import datetime
from atproto import Client, models
from nanoatp.richtext import detectLinks

MANUAL = os.getenv("MANUAL", "")
IS_DEPLOYED = os.getenv("IS_DEPLOYED", "")
WMATA_API_KEY = os.getenv("WMATA_API_KEY")
BOT_HANDLE = os.getenv("BOT_HANDLE")
BOT_APP_PASSWORD = os.getenv("BOT_APP_PASSWORD")

MAX_POSTS_PER_RUN = 5

# Vercel KV related args for state keeping.
VERCEL_KV_URL = os.getenv("VERCEL_KV_URL")
VERCEL_KV_REST_API_URL = os.getenv("VERCEL_KV_REST_API_URL")
VERCEL_KV_REST_API_TOKEN = os.getenv("VERCEL_KV_REST_API_TOKEN")
VERCEL_KV_REST_API_READ_ONLY_TOKEN = os.getenv("VERCEL_KV_REST_API_READ_ONLY_TOKEN")

at_client = None
kv_client = None


def check_facets(facets: list):
    """ Examples of offending facet:
    Incorrectly ends in period
    [{'$type': 'app.bsky.richtext.facet', 'index': {'byteStart': 149, 'byteEnd': 178}, 'features': [{'$type': 'app.bsky.richtext.facet#link', 'uri': 'https://buseta.wmata.com/#36.'}]}]

    "Mt.Vernon" is not a valid uri but naively looks like one
    [{'$type': 'app.bsky.richtext.facet', 'index': {'byteStart': 148, 'byteEnd': 157}, 'features': [{'$type': 'app.bsky.richtext.facet#link', 'uri': 'Mt.Vernon'}]}]
    """
    fixed = []
    for facet in facets:
        # if url lacks http:// or https://, manually include it
        if facet['features'][0]['uri'].find("http://") == -1 and facet['features'][0]['uri'].find("https://") == -1:
            print(f"Fixing facet for uri: {facet['features'][0]['uri']}")
            facet['features'][0]['uri'] = f"https://{facet['features'][0]['uri']}"
            print(f"Fixed uri: {facet['features'][0]['uri']}")
            fixed.append(facet)
        # If url ends in a dot we accidentally matched a period
        if facet['features'][0]['uri'][-1] == '.':
            print(f"Fixing facet for uri: {facet['features'][0]['uri']}")
            # Move end byte back by one
            facet['index']['byteEnd'] -= 1
            # Take slice to skip the last character
            facet['features'][0]['uri'] = facet['features'][0]['uri'][:-1]
            print(f"Fixed uri: {facet['features'][0]['uri']}")
            fixed.append(facet)
        elif facet['features'][0]['uri'].lower() == "Mt.Vernon".lower():
            # Not an actual url so skip this one.
            pass
        # elif facet['features'][0]['uri'].lower() == "N.W.".lower():
        #     # Not an actual url so skip this one.
        #     pass
        else:
            # Nothing to fix
            fixed.append(facet)
    return fixed


def send_post(text: str):
    """Send post with the given text content
    return post_ref of generated post
    """
    print(f"Sending post with text:\n{text}")
    if at_client is None:
        at_login()

    # Make links clickable via rich text facets
    # Facet model structure:
    # facets = [
    #     models.AppBskyRichtextFacet.Main(
    #         features=[models.AppBskyRichtextFacet.Link(uri=url)],
    #         # Indicate the start and end of link in text
    #         index=models.AppBskyRichtextFacet.ByteSlice(byteStart=link_start, byteEnd=link_end)
    #     )
    # ]
    facets = detectLinks(text)
    # NOTE: sometimes finds urls with bogus trailing dots (bc of WMATA info like "wmata.com.")
    print(f"Found rich text facets: {facets}")
    facets = check_facets(facets)
    print(f"Adjusted rich text facets: {facets}")

    try:
        if IS_DEPLOYED or MANUAL:
            # Only bother embedding facets if there's a url.
            if len(facets) == 0:
                at_client.send_post(text=text)
            else:
                # Manually create post record to include rich text facets
                at_client.com.atproto.repo.create_record(
                    models.ComAtprotoRepoCreateRecord.Data(
                        repo=at_client.me.did,
                        collection=models.ids.AppBskyFeedPost,
                        record=models.AppBskyFeedPost.Main(
                            createdAt=datetime.now().isoformat(), text=text, facets=facets
                        )
                    )
                )
        else:
            print("Skipping sending post...")
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
    print("Logged in as: ", profile.display_name)


def is_newer(update_time: Union[str, datetime], last_posted: Optional[Union[str, datetime]]) -> bool:
    """Determine if update_time is more recent than the retrieved"""
    if last_posted is None or last_posted == "":
        return True  # TODO: is this a safe default or do we risk spamming?
    if not isinstance(update_time, datetime):
        update_time = datetime.fromisoformat(update_time)
    if not isinstance(last_posted, datetime):
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


# def login_kv():
#     global kv_client
#     kv_client = KV(
#         kv_config=KVConfig(
#             url=VERCEL_KV_URL,
#             rest_api_url=VERCEL_KV_REST_API_URL,
#             rest_api_token=VERCEL_KV_REST_API_TOKEN,
#             rest_api_read_only_token=VERCEL_KV_REST_API_READ_ONLY_TOKEN
#         )
#     )


def get_latest_post_time():
    """ Time corresponds to WMATA update time, not post time.
    Example reponse:
    Response(
        feed=[
            FeedViewPost(
                post=PostView(author=ProfileViewBasic(did='did:plc:4fzw4vfbpsdy77d6jvtmpxgk', handle='wmata-incidents.bsky.social', avatar='https://cdn.bsky.social/imgproxy/hteEyCauUcf07g7DRZ1TVjd6NjiDIpp68dEqlML7nD4/rs:fill:1000:1000:1:0/plain/bafkreicptnkurw36wwvqe5nqqd5ebwo7uq5yynwt4v4x72icn4v4irxqdq@jpeg', displayName='WMATA Incidents', labels=[], viewer=ViewerState(blockedBy=False, blocking=None, followedBy=None, following=None, muted=False, mutedByList=None, _type='app.bsky.actor.defs#viewerState'), _type='app.bsky.actor.defs#profileViewBasic'), cid='bafyreiezwte44vksso53ltnl5f7tkrlpnxeiqo3tukkjmmjlzeixth66xe', indexedAt='2023-07-26T02:04:52.699Z', record=Main(createdAt='2023-07-26T02:04:52.640687', text='Bus incident reported affecting the following routes: 36.\n\n    Alert: Route 36 westbound on detour at Naylor Rd & Suitland Pkwy, resuming regular route at Naylor Rd & 30th St.\n\n    Last updated: 2023-07-25 21:35:06 (Eastern Time).', embed=None, entities=None, facets=None, langs=['en'], reply=None, _type='app.bsky.feed.post'), uri='at://did:plc:4fzw4vfbpsdy77d6jvtmpxgk/app.bsky.feed.post/3k3fd4zfdza2d', embed=None, labels=[], likeCount=0, replyCount=0, repostCount=0, viewer=ViewerState(like=None, repost=None, _type='app.bsky.feed.defs#viewerState'), _type='app.bsky.feed.defs#postView'), reason=None, reply=None, _type='app.bsky.feed.defs#feedViewPost'
            )
        ],
        cursor='1690337092640::bafyreiezwte44vksso53ltnl5f7tkrlpnxeiqo3tukkjmmjlzeixth66xe'
    )
    """
    if at_client is None:
        at_login()

    # Fetch feed of latest posts from this bot
    feed_resp = at_client.app.bsky.feed.get_author_feed({"actor": BOT_HANDLE, "limit": 1})
    print(f"Got feed response:\n{feed_resp}")
    # Get post itself
    latest_post = feed_resp.feed[0].post
    # Get text from the post
    post_text: str = latest_post.record.text
    print(f"Got latest post with text:\n{post_text}")
    # Get post by lines
    post_lines = post_text.splitlines()
    # Get update line: "Updated: 2023-07-25 20:10:19 (Eastern Time)."
    update_line = post_lines[-1]
    print(f"Post update line reads: {update_line}")
    # Get timestamp from within this line: "2023-07-25 20:10:19"
    time_string = update_line[update_line.find(": ")+len(": "): update_line.find("(")-len("(")]
    # Convert to datetime object for comparisons
    timestamp = datetime.fromisoformat(time_string)

    return timestamp


def find_new_incidents(incident_list, latest_post: datetime):
    """Collect new / updated incidents based on kv records
    """
    new_incidents = []
    # if kv_client is None:
    #     login_kv()

    # Active incidents are listed in reverse chronological order, reverse for posting.
    incident_list.reverse()
    for incident in incident_list:
        if is_newer(incident["DateUpdated"], latest_post):
            print("Found new incident for processing...")
            new_incidents.append(incident)
        elif not IS_DEPLOYED and not MANUAL:
            print("Appending old incident due to development config...")
            new_incidents.append(incident)

    # TODO: remove if we're confident the previous method performs just as well.
    # if kv_client.has_auth():
    #     # Active incidents are listed in reverse chronological order, reverse for posting.
    #     incident_list.reverse()
    #     for incident in incident_list:
    #         last_posted_update = kv_client.get(incident["IncidentID"])
    #         # TODO: what happens if the key has never been used? returns '{"result":null}' i.e. None?
    #         if is_newer(incident["DateUpdated"], last_posted_update):
    #             new_incidents.append(incident)
    #         elif not IS_DEPLOYED:
    #             print("Appending old post due to debug config")
    #             new_incidents.append(incident)
    # else:
    #     print("Unable to access kv store to check incident history! Skipping to avoid post spam!")
    return new_incidents


# def update_last_posted(incident_id, date_updated):
#     """Store last updated time for this incident id in kv.
#     """
#     if kv_client is None:
#         login_kv()

#     if kv_client.has_auth():
#         kv_client.set(incident_id, date_updated)
#     else:
#         print("Unable to access kv store to check incident history! Warning may post spam!")


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

    return dedent(f"""
Train incident reported for lines: {line_format(incident_dict['LinesAffected'])}.
{incident_dict['IncidentType']}: {incident_dict['Description']}
Updated: {datetime.fromisoformat(incident_dict['DateUpdated'])} (Eastern).
""").strip()


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
    return dedent(f"""
Bus incident reported for routes: {','.join(incident_dict['RoutesAffected'])}.
{incident_dict['IncidentType']}: {incident_dict['Description']}
Updated: {datetime.fromisoformat(incident_dict['DateUpdated'])} (Eastern).
""").strip()


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
            'EstimatedReturnToService': '2023-09-04T23:59:59' // Somestimes is None TODO: add test for this
        }]
    }
    """
    def return_date(incident_dict: dict) -> str:
        date = incident_dict['EstimatedReturnToService']
        if date is not None:
            return datetime.fromisoformat(date)
        else:
            return str(date)

    return dedent(f"""
Elevator incident reported at: {incident_dict['StationName']}.
{incident_dict['SymptomDescription']}: {incident_dict['LocationDescription']}.
Estimated return: {return_date(incident_dict)} (Eastern).
Updated: {datetime.fromisoformat(incident_dict['DateUpdated'])} (Eastern).
""").strip()


def main():
    print(f"Cron has been invoked at {datetime.now()}")
    # Note: Assumes the invarient "latest post has the latest WMATA update time"
    latest_update = get_latest_post_time()
    print(f"Latest post was an update from {latest_update}")

    # Step 0: generate auth header
    wmata_header = {"api_key": WMATA_API_KEY}

    # Step 1: Check incidents
    train_resp = requests.get(url="https://api.wmata.com/Incidents.svc/json/Incidents", headers=wmata_header)
    bus_resp = requests.get(url="https://api.wmata.com/Incidents.svc/json/BusIncidents", headers=wmata_header)
    elevator_resp = requests.get(url="https://api.wmata.com/Incidents.svc/json/ElevatorIncidents", headers=wmata_header)

    print("Got train incident response: ", train_resp.json())
    print("Got bus incident response: ", bus_resp.json())
    print("Got elevator incident response: ", elevator_resp.json())

    # Step 2: Collect relevant incidents (check latest_update for recency)
    new_train = find_new_incidents(train_resp.json()['Incidents'], latest_update)
    new_bus = find_new_incidents(bus_resp.json()['BusIncidents'], latest_update)
    # new_elevator = find_new_incidents(elevator_resp.json()['ElevatorIncidents'], latest_update)

    print(f"Got {len(new_train)} new train incidents")
    print(f"Got {len(new_bus)} new bus incidents")
    # print(f"Got {len(new_elevator)} elevator incidents")

    # Step 3: Generate posts to send (post_text, date_updated)
    to_send: list[tuple[str, str]] = []
    to_send.extend(
        [(make_train_incident_text(incident), incident['DateUpdated']) for incident in new_train]
        )
    to_send.extend(
        [(make_bus_incident_text(incident), incident['DateUpdated']) for incident in new_bus]
        )
    # to_send.extend(
    #     [(make_elevator_incident_text(incident), '_', incident['DateUpdated']) for incident in new_elevator]
    #     )

    # Step 4: Send posts and update last post time in kv.
    posts = 0
    latest_post = None
    # Sort posts overall by the datetime of their update (newest last)
    to_send.sort(key=lambda a: a[1])
    for post_tuple in to_send:
        if posts >= MAX_POSTS_PER_RUN and (IS_DEPLOYED or MANUAL):
            print(f"Sent {MAX_POSTS_PER_RUN} posts, stopping to avoid spamming. {len(to_send)-MAX_POSTS_PER_RUN} to go next time.")
            break
        if not IS_DEPLOYED or MANUAL:
            # Pause before posting during development
            breakpoint()
        if send_post(post_tuple[0]):
            posts += 1
            latest_post = post_tuple[1]
        else:
            print("Post failed! Moving on...")

    # Will look this time up via atproto on next run.
    # Note: we post the most recent update last to uphold invarient.
    print(f"Lastest post was from timestamp: {latest_post}.")
    print(f"Sent {posts} incident posts. Exiting...")


if __name__ == "__main__":
    main()
