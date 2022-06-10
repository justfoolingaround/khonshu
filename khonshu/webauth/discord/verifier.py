API_ENDPOINT = "https://discord.com/api/v10/users/@me"


def get_discord(session, token):
    me = session.get(API_ENDPOINT, headers={"authorization": token})

    if me.status_code != 200:
        return {}

    return me.json()
