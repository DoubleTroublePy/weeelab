# A perfect candidate for dataclasses... which may not be available on an old Python version.
# So no dataclasses.
class User:
	def __init__(self, username: str, full_name: str, first_name: str, signed_sir: bool):
		self.username = username
		self.full_name = full_name
		self.first_name = first_name
		self.signed_sir = signed_sir


class LdapError(BaseException):
	def __init__(self):
		pass


class UserNotFoundError(BaseException):
	def __init__(self):
		pass

def get_user(username: str) -> User:
	found = False
	ambiguous = False
	matricolized = matricolize(username)
	username = escape_filter_chars(username)
	if matricolized is None:
		filters = (
			f"(&(objectClass=weeeOpenPerson)(uid={username})(!(nsaccountlock=true)))",
			f"(&(objectClass=weeeOpenPerson)(weeelabnickname={username})(!(nsaccountlock=true)))"
		)
	else:
		filters = (
			f"(&(objectClass=weeeOpenPerson)(schacpersonaluniquecode={matricolized})(!(nsaccountlock=true)))",
		)
	del matricolized

	try:
		# print(f"Asking {LDAP_SERVER} for info...")
		conn = ldap.initialize(LDAP_SERVER)
		conn.protocol_version = ldap.VERSION3
		if LDAP_SERVER.startswith('ldap://'):
			conn.start_tls_s()
		conn.simple_bind_s(LDAP_BIND_DN, LDAP_PASSWORD)
	except ldap.SERVER_DOWN:
		print(f"Cannot connect to LDAP server {LDAP_SERVER}")
		raise LdapError
	if conn is None:
		print(f"Error connecting to LDAP server :(")
		raise LdapError

	for the_filter in filters:
		result = conn.search_s(LDAP_TREE, ldap.SCOPE_SUBTREE, the_filter, (
			'uid',
			'cn',
			'givenname',
			'signedsir'
		))
		if len(result) > 1:
			ambiguous = True
		if len(result) == 1:
			attr = result[0][1]
			if 'signedsir' in attr:
				signed_sir = attr['signedsir'][0].decode().lower() == 'true'
			else:
				signed_sir = False
			return User(attr['uid'][0].decode(), attr['cn'][0].decode(), attr['givenname'][0].decode(), signed_sir)
	conn.unbind_s()

	if ambiguous:
		print(f"Multiple accounts found for that username/matricola/nickname, try with another one.")
		raise UserNotFoundError
	if not found:
		print(f"Username not recognized. Maybe you misspelled it or you're an intruder.")
		raise UserNotFoundError

