import requests
import re
import json
import html
from getenv import env

# All BILL accounts are connected to a specific LDAP username.
# Let's use this fact to connect Members to BILL accounts,
# instead of storing the account number separately.

class BILLException(Exception):
    pass

ERROR_NO_BILL = BILLException("BILL is not set up")
ERROR_ACCOUNT_DOES_NOT_EXIST = BILLException("BILL account does not exist")

def admin_url(bill_id):
    api_url = env("BILL_API_URL")
    if not api_url:
        raise ERROR_NO_BILL
    return f'{"/".join(api_url.split("/")[:-2])}/admin/userdata?id={bill_id}'

def __request(path):
    api_url = env("BILL_API_URL")
    user = env("BILL_API_USER")
    password = env("BILL_API_PW")
    if not all([api_url, user, password]):
        raise ERROR_NO_BILL

    try:
        r = requests.post(api_url + path, auth=(user, password))
    except:
        raise BILLException("Could not connect to BILL server")

    if r.status_code != 200:
        raise BILLException(f"BILL returned status code: {r.status_code}")

    # The response can be anything, and it's up to the caller to parse it correctly.
    # If not a number, return as text.
    try:
        number = int(r.text)
    except ValueError:
        # BILL uses HTML ecoding to represent non-ASCII characters
        return html.unescape(r.text)

    # A negative number means an error code
    if number == -3:
        raise ERROR_ACCOUNT_DOES_NOT_EXIST
    if number < 0:
        raise BILLException(f"BILL returned error code: {number}")

    # A non-negative number is a valid response
    return number

def create_account(username):
    if not re.search(r'^[A-Za-z0-9]+$', username):
        raise BILLException("Can not create a BILL account using an LDAP username containing anything other than letters and numbers")

    result = __request(f"add?type=user&id={username}")
    if type(result) == int:
        return result
    raise BILLException(f"BILL returned error: {result}")

def delete_account(username):
    # If the BILL account does not exist all is ok
    if not get_account(username):
        return

    result = __request(f"del?type=user&id={username}")
    if result != 0:
        raise BILLException(f"BILL returned error: {result}")

def get_account(username):
    '''
    Get the info for the BILL account connected to a certain LDAP username.
    Returns None if the account does not exist.
    '''
    try:
        result = __request(f"get?type=user&id={username}")
        info = json.loads(result)
        info['acc'] = int(info['acc'])
        # Balance is a float, but leave it as a string to avoid having to format it later
        # info['balance'] = float(info['balance'])
        return info
    except BILLException as e:
        if e == ERROR_ACCOUNT_DOES_NOT_EXIST:
            return None
        raise e
