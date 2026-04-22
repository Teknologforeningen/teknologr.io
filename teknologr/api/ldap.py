import ldap
import ldap.modlist
from getenv import env
from teknologr.settings import AUTH_LDAP_MIN_UID as MIN_UID, AUTH_LDAP_PAGE_SIZE as PAGE_SIZE

import time

'''All methods here can throw ldap.LDAPError'''

def LDAPError_to_string(e):
    if not isinstance(e, ldap.LDAPError):
        return str(e)
    data = e.args[0]
    s = f"{data.get('desc' , '')} [LDAP result code {data.get('result')}]"
    info = data.get('info')
    if info:
        s += f' ({info})'
    return s

class LDAPAccountManager:
    def __init__(self):
        # Don't require certificates
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        # Attempts no connection, simply initializes the object.
        self.ldap = ldap.initialize(env("LDAP_SERVER_URI", "ldaps://localhost:45671"))

    def __enter__(self):
        self.ldap.simple_bind_s(
            env("LDAP_ADMIN_BIND_DN", "admin"),
            env("LDAP_ADMIN_PW", "hunter2")
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.ldap.unbind_s()

    def add_account(self, member, username, password):
        # Adds new account for the given member with the given username and password
        dn = env("LDAP_USER_DN_TEMPLATE") % {'user': username}

        uidnumber = self.get_next_uidnumber()
        nt_pw = self.get_samba_password(password)

        # Everything has to be byte string because why the fuck not?
        attrs = {}
        attrs['uid'] = [username.encode('utf-8')]
        attrs['cn'] = [member.common_name.encode('utf-8')]
        homedir = '/rhome/%s' % username
        attrs['homeDirectory'] = [homedir.encode('utf-8')]
        attrs['uidNumber'] = [str(uidnumber).encode('utf-8')]
        attrs['mailHost'] = [b'smtp.ayy.fi']
        attrs['gidNumber'] = [b'1000']
        attrs['sn'] = [member.surname.encode('utf-8')]
        attrs['givenName'] = [member.get_preferred_name().encode('utf-8')]
        attrs['loginShell'] = [b'/bin/bash']
        attrs['objectClass'] = [
            b'kerberosSecurityObject',
            b'inetOrgPerson',
            b'posixAccount',
            b'shadowAccount',
            b'inetLocalMailRecipient',
            b'top',
            b'person',
            b'organizationalPerson',
            b'billAccount',
            b'sambaSamAccount'
        ]
        attrs['krbName'] = [username.encode('utf-8')]
        attrs['mail'] = [member.email.encode('utf-8')]
        attrs['userPassword'] = [self.hash_user_password(password)]
        sambasid = "S-1-0-0-%s" % str(uidnumber*2+1000)
        attrs['sambaSID'] = [sambasid.encode('utf-8')]
        attrs['sambaNTPassword'] = [nt_pw.encode('utf-8')]
        attrs['sambaPwdLastSet'] = [str(int(time.time())).encode('utf-8')]

        # Add the user to LDAP
        ldif = ldap.modlist.addModlist(attrs)
        self.ldap.add_s(dn, ldif)

        # Add user to Members group
        group_dn = env("LDAP_MEMBER_GROUP_DN")
        self.ldap.modify_s(group_dn, [(ldap.MOD_ADD, 'memberUid', username.encode('utf-8'))])

    def for_each_user(self, cb, attrlist = None):
        """
        Helper function for fetching all LDAP users. Fetching of users are made in batches, because the total amount of users might exceed the LDAP server's size limit for queries. Hitting the size limit gives LDAPError code 4 (Size Limit Exceeded).

        `cb` is a callback function that is called for each fetched user. If the callback returns falsy, the iteration is stopped prematurely.
        `attrlist` is a list of attributes to fetch for each user.

        It would be nice to use the built-in pagination, but that does not seem to circumvent the size limit...
        Example:
            from ldap.controls import SimplePagedResultsControl
            serverctrls = [ SimplePagedResultsControl(True, size=PAGE_SIZE, cookie=b'') ]
            ...

        On a related note, it would also be nice to use server-side sorting for this. In that case each batch could simply use a lower-bound for uidNumber, and use the `sizelimit=` argument in `search_ext_s` to limit the number of results. If the server sorted the results, it would be easy to get the next lower-bound from the last result and redo the query until all users have been fetched. However, our LDAP server does (currently) not support server-side sorting, and the `sizelimit=` argument does not seem to work either (or maybe I'm just doing something wrong)...
        Example:
            from ldap.controls.sss import SSSRequestControl
            serverctrls = [ SSSRequestControl(True, ['uidNumber']) ]
            ...

        XXX: Implement pagination for other queries too?
        """

        first = MIN_UID
        limit = PAGE_SIZE

        while True:
            # Filter for all but the last query:
            #   first <= uidNumber <= first + limit - 1
            # Filter for the last query:
            #   first <= uidNumber
            filterstr = f'(&(uidNumber>={first})'
            if limit:
                filterstr += f'(uidNumber<={first + limit - 1})'
            filterstr += ')'

            first += limit

            users = self.ldap.search_ext_s(
                env("LDAP_USER_DN"),
                ldap.SCOPE_ONELEVEL,
                filterstr=filterstr,
                attrlist=attrlist or ["uid", "uidNumber"],
            ) or []

            for user in users:
                # user is ('uid=XXX,cn=...', { attrs })
                if not cb(user[1]):
                    return

            if not limit:
                return

            # Arbitrary heuristic to decide when to remove the limit and make the last query
            if len(users) < limit/2:
                limit = 0

    def get_next_uidnumber(self):
        uids = []

        def cb(user):
            uids.append(int(self.__get_key(user, 'uidNumber') or 0))
            return True

        self.for_each_user(cb, ['uidNumber'])
        uids.sort()

        last = MIN_UID - 1
        for uid in uids:
            if uid > last + 1:
                break
            last = uid
        return last + 1

    def check_account(self, username):
        '''
        Check if a certain LDAP account exists.
        '''
        try:
            dn = env("LDAP_USER_DN_TEMPLATE") % {'user': username}
            self.ldap.search_s(dn, ldap.SCOPE_BASE)
            return True
        except ldap.LDAPError as e:
            # Result code 32 = noSuchObject
            if e.args[0].get('result') == 32:
                return False
            raise e

    def delete_account(self, username):
        # Remove user from the members LDAP group, but do not throw if the user it not part of it
        try:
            group_dn = env("LDAP_MEMBER_GROUP_DN")
            self.ldap.modify_s(group_dn, [(ldap.MOD_DELETE, 'memberUid', username.encode('utf-8'))])
        except ldap.LDAPError as e:
            # Result code 16 = noSuchAttribute
            if e.args[0].get('result') != 16:
                raise e

        # Removing non-existent user would fail, so checking that first
        if self.check_account(username):
            dn = env("LDAP_USER_DN_TEMPLATE") % {'user': username}
            self.ldap.delete_s(dn)

    def change_password(self, username, password):
        # Changes both the user password and the samba password
        dn = env("LDAP_USER_DN_TEMPLATE") % {'user': username}
        nt_pw = self.get_samba_password(password)
        mod_attrs = [
            (ldap.MOD_REPLACE, 'userPassword', self.hash_user_password(password)),
            (ldap.MOD_REPLACE, 'sambaNTPassword', nt_pw.encode('utf-8'))
        ]
        self.ldap.modify_s(dn, mod_attrs)

    def change_email(self, username, email):
        # Changes the email address for the given user
        dn = env("LDAP_USER_DN_TEMPLATE") % {'user': username}
        mod_attrs = [
            (ldap.MOD_REPLACE, 'mail', email.encode('utf-8')),
        ]
        self.ldap.modify_s(dn, mod_attrs)

    def get_samba_password(self, password):
        # The password needs to be stored in a different format for samba
        import codecs
        import hashlib
        return codecs.encode(
            hashlib.new('md4', password.encode('utf-16le')).digest(), 'hex_codec'
        ).decode('utf-8').upper()

    def hash_user_password(self, password):
        import random
        import string
        import hashlib
        import base64
        import binascii
        salt = "".join([random.choice(string.ascii_uppercase) for i in range(4)])
        digest = hashlib.md5((password + salt).encode('utf-8')).hexdigest()
        return b"{SMD5}" + base64.b64encode(binascii.unhexlify(digest) + salt.encode('utf-8'))

    def __get_key(self, d, key, default=None):
        value = d.get(key)
        if value is None:
            return default
        return value[0].decode('utf-8')

    def get_user_list(self):
        usernames = []

        def cb(user):
            usernames.append(self.__get_key(user, 'uid'))
            return True

        self.for_each_user(cb, ['uid'])
        return sorted(usernames)

    def get_user_details(self, username):
        result = self.ldap.search_s(
            env('LDAP_USER_DN'),
            ldap.SCOPE_ONELEVEL,
            f'(uid={username})',
            ['uidNumber', 'givenName', 'sn', 'mail'])
        if not result:
            return None
        user = result[0][1]
        id = self.__get_key(user, 'uidNumber', '')
        return {
            'username': username,
            'id': int(id) if id.isdecimal() else None,
            'given_name': self.__get_key(user, 'givenName'),
            'surname': self.__get_key(user, 'sn'),
            'email': self.__get_key(user, 'mail'),
            'groups': self.get_user_groups(username),
        }

    def get_user_groups(self, username):
        result = self.ldap.search_s(
            env('LDAP_GROUP_DN'),
            ldap.SCOPE_SUBTREE,
            f'(&(objectClass=posixGroup)(memberUid={username}))',
            ['cn'])
        return sorted([self.__get_key(group[1], 'cn') for group in result])

    def get_group_list(self):
        result = self.ldap.search_s(
            env('LDAP_GROUP_DN'),
            ldap.SCOPE_ONELEVEL,
            '(objectClass=posixGroup)',
            ['cn'])
        return sorted([self.__get_key(group[1], 'cn') for group in result])

    def get_group_details(self, group_name):
        result = self.ldap.search_s(
            env('LDAP_GROUP_DN'),
            ldap.SCOPE_ONELEVEL,
            f'(&(objectClass=posixGroup)(cn={group_name}))',
            ['gidNumber', 'description', 'memberUid'])
        if not result:
            return None
        group = result[0][1]
        id = self.__get_key(group, 'gidNumber', '')
        return {
            'name': group_name,
            'description': self.__get_key(group, 'description'),
            'id': int(id) if id.isdecimal() else None,
            'members': group.get('memberUid', []),
        }
