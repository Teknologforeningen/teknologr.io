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
        r = requests.post(api_url + path, auth=(str(user), str(password)))
    except:
        raise BILLException("Could not connect to BILL server")

    if r.status_code != 200:
        raise BILLException(f"Request to BILL API returned status code {r.status_code}")

    # The response can be anything, and it's up to the caller to parse it correctly.
    # If not a number, return as text.
    # Negatvie numbers are in general error codes, but they are not necessarily the same across endpoints.
    try:
        number = int(r.text)
        return number
    except ValueError:
        # BILL uses HTML ecoding to represent non-ASCII characters
        return html.unescape(r.text)

def create_account(username):
    if not re.search(r'^[A-Za-z0-9]+$', username):
        raise BILLException("Can not create a BILL account using an LDAP username containing anything other than letters and numbers")

    '''
    Possible return values:
      >0: Success, id of the new account
      -1: Request invalid, missing or invalid type=
      -2: Request invalid, missing or invalid id=
      -3: Request invalid, missing name= (not required for type=user)
      -4: Account already exists
      -5: Creation failed
      -6: Internal error
    '''
    result = __request(f"add?type=user&id={username}")

    if type(result) == int and result > 0:
        return result
    raise BILLException(f"BILL returned error: {result}")

def delete_account(username):
    # If the BILL account does not exist all is ok
    if not get_account(username):
        return

    '''
    Possible return values:
       0: Success
      -1: Request invalid, missing or invalid type=
      -2: Request invalid, missing both id= and acc=
      -3: Account does not exist
      -4/-5/-6: Internal error
    '''
    result = __request(f"del?type=user&id={username}")

    if result != 0:
        raise BILLException(f"BILL returned error: {result}")

def get_account(username):
    '''
    Get the info for the BILL account connected to a certain LDAP username.
    Returns None if the account does not exist.
    '''

    '''
    Possible return values:
      JSON-encoded string: Success, account information with the format { type, acc, id, name, nick, balance } with all values being strings (nick can also be null)
      -1: Request invalid, missing or invalid type=
      -2: Request invalid, missing both id= and acc=
      -3: Account does not exist
    '''
    result = __request(f"get?type=user&id={username}")

    if result == -3:
        return None
    if type(result) == int:
        raise BILLException(f"BILL returned error: {result}")

    info = json.loads(str(result))
    info['acc'] = int(info['acc'])
    # Balance is a float, but leave it as a string to avoid having to format it later
    # info['balance'] = float(info['balance'])
    return info

def get_key(username):
    '''
    Get the number of the Generikey key tied to a user.
    Returns None if no key was found.
    '''

    '''
    Possible return values:
      >=0: Success, key number
      -1: Username validation failed
      -2: Account does not exist
      -3: No key tied to account
    '''
    result = __request(f"key?user={username}")

    if type(result) == int:
        if result >= 0:
            return result
        if result == -2 or result == -3:
            return None
    raise BILLException(f"BILL returned error: {result}")
