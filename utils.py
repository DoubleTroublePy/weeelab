from typing import Optional
from getpass import getuser
import user

# utils
def secure_exit(return_value=0):
	"""
	Terminate the program being sure about undoing some changes like CLI color

	:param return_value: return this to the caller
	"""
	sys.stdout.write(COLOR_NATIVE)
	sys.exit(return_value)


def check_date(input_date: str) -> bool:
	"""
	Check if date is in the right format

	:param input_date: Some representation of a date
	:return: True if valid, false otherwise
	"""
	date = input_date.split("/")

	if len(date[0]) != 2 or len(date[1]) != 2 or len(date[2]) != 4:
		print("date format error")
		return False
	return True


def check_hour(input_hour: str) -> bool:
    """
    Check if hour is in the right format

    :param input_hour:
    :return:
    """
    hour = input_hour.split(":")
    if len(hour) != 2:
        print("wrong hour format")
        return False
    return True


def matricolize(username: str):
    """
    Take a username and turn it in a matricole number

    :param username: of the user
    :return matricole: number
    """
    if username.isdigit():
        return f"s{username}"

    if username[1:].isdigit() and username[0] in ('s', 'S', 'd', 'D'):
        return username
    return None

def is_logged_in(username: str) -> bool:
	"""
	Check if user is already logged in.

	:param username: normalized username
	:return:
	"""
	logged = False
	with open(LOG_FILENAME, "r") as log_file:
		for line in log_file:
			if inlab_line(line) and user_in_line(line, username):
				logged = True
				break
	return logged


def people_in_lab() -> int:
	count = 0
	with open(LOG_FILENAME, "r") as log_file:
		for line in log_file:
			if inlab_line(line):
				count += 1
	return count


def is_empty(input_file) -> bool:
	"""
	Check if inputFile is empty.

	:param input_file:
	:return:
	"""
	if str(input_file.read())[:1] == "":
		input_file.close()
		return True
	else:
		input_file.seek(0)
		return False


def ensure_log_file():
	if not os.path.exists(LOG_FILENAME):
		if os.path.isdir(os.path.dirname(LOG_FILENAME)):
			print(f"Creating empty log.txt")
			open(LOG_FILENAME, "a").close()
		else:
			print(f"Cannot find directory {os.path.dirname(LOG_FILENAME)}")
			secure_exit(1)


def store_log_to(filename, destination):
	"""
	Copy a log file (or anything, really) to a directory, if DEBUG_MODE is False

	:param filename: Path to source file
	:param destination: Path to destination file or directory
	"""
	if DEBUG_MODE:
		print(f"DEBUG_MODE, skipped copying {os.path.basename(filename)} to {destination}")
	else:
		copy2(filename, destination)


def create_backup_if_necessary():
	# Open master log file
	with open(LOG_FILENAME, "r") as log_file:
		if not is_empty(log_file):  # If current log file is not empty
			last_month_year = str(log_file.read())[4:11]

			curr_month = int(datetime.now().strftime("%m"))
			curr_year = int(datetime.now().strftime("%Y"))
			last_date = datetime.strptime(last_month_year, "%m/%Y")
			last_month = int(last_date.strftime("%m"))
			last_year = int(last_date.strftime("%Y"))

			# If the inexorable passage of time has been perceived by this program, too...
			if (curr_month > last_month) or (curr_year > last_year):
				# log.txt -> log201901.txt, foo.txt -> foo201901.txt, etc...
				stored_log_filename = LOG_FILENAME.rsplit('.', 1)[0] + last_date.strftime("%Y%m") + ".txt"
				print(f"Backing up log file to {os.path.basename(stored_log_filename)}")
				os.rename(LOG_FILENAME, stored_log_filename)
				# store_log_to(stored_log_filename, BACKUP_PATH)
				# print(f"Done!")

				open(LOG_FILENAME, "a").close()
				print(f"New log file was created.")

def login(username: str, use_ldap: bool):
	"""
	Log in. Add the line in the file. Do it.

	:param use_ldap: Connect to remote LDAP server or blindly trust the input
	:param username: User-supplied username
	"""

	lab_was_empty = people_in_lab() == 0

	if use_ldap:
		user = get_user(username)
		username = user.username
		pretty_name = user.full_name
		check_sir(user)
	else:
		print(COLOR_RED)
		print("WARNING: bypassing LDAP lookup, make sure that this is the correct username and not an alias")
		print(COLOR_NATIVE)
		pretty_name = username

	if is_logged_in(username):
		print(f"{pretty_name}, you're already logged in.")
	else:
		curr_time = datetime.now().strftime("%d/%m/%Y %H:%M")
		login_string = f"[{curr_time}] [----------------] [INLAB] <{username}>\n"
		with open(LOG_FILENAME, "a") as log_file:
			log_file.write(login_string)

		# store_log_to(LOG_FILENAME, BACKUP_PATH)

		if lab_was_empty:
			global FIRST_IN_HAPPENED
			FIRST_IN_HAPPENED = True
		print(f"Login successful! Hello {pretty_name}!")


def logout(username: str, use_ldap: bool, message: Optional[str] = None):
	"""
	Log out.

	:param message: Logout message, None to ask
	:param use_ldap: Connect to remote LDAP server or blindly trust the input
	:param username: User-supplied username
	"""

	last_person = people_in_lab() == 1

	if not use_ldap:
		print(COLOR_RED)
		print("WARNING: bypassing LDAP lookup, make sure that this is the correct username and not an alias")
		print(COLOR_NATIVE)

	if is_logged_in(username):
		# Using username, and found
		pretty_name = username
	else:
		# Not found, is it an alias?
		if use_ldap:
			# Grab the real username
			user = get_user(username)
			new_username = user.username
			pretty_name = user.full_name
			check_sir(user)
			if username == new_username or not is_logged_in(new_username):
				print(f"You aren't in lab! Did you forget to log in?")
				return False
			username = new_username
		else:
			# Cannot get it from LDAP
			print(f"You aren't in lab! Did you use an alias or ID number? These do not work right now")
			return False

	curr_time = datetime.now().strftime("%d/%m/%Y %H:%M")
	if message is None:
		workdone = ask_work_done()
	else:
		workdone = message

	if write_logout(username, curr_time, workdone):
		if last_person:
			global LAST_OUT_HAPPENED
			LAST_OUT_HAPPENED = True
		print(f"Logout successful! Bye {pretty_name}!")
		return True
	else:
		print(f"Logout failed")
		return False


def check_sir(user):
	global SIR_HAPPENED
	SIR_HAPPENED = not user.signed_sir


def ask_work_done():
	try:
		ok = False
		workdone = ""
		while not ok:
			workdone = input(f"What have you done?\n:: ").strip()
			if len(workdone) > MAX_WORK_DONE:
				print(f"I didn't ask you the story of your life! Type a shorter sentence!")
			elif len(workdone) <= 0:
				print(f"Come on, tell me something! How was your day?")
			else:
				ok = True
	except KeyboardInterrupt:
		print(f"Logout cancelled by keyboard interrupt")
		secure_exit(5)
		return None  # Just prevents PyCharm from complaining
	return workdone


def work_time(timein, timeout) -> str:
	"""
	Returns the time spent in lab formatted as HH:MM
	"""
	li = (int(timein[:2]) * 60) + int(timein[3:5])
	lo = (int(timeout[:2]) * 60) + int(timeout[3:5])
	hours = int((lo - li) / 60)
	minutes = int((lo - li) % 60)
	return str(hours).zfill(2) + ":" + str(minutes).zfill(2)


def inlab_line(line: str) -> bool:
	# [02/05/2017 10:00] [----------------] [INLAB] :: <
	return line[39:44] == "INLAB"


def user_in_line(line: str, username: str) -> bool:
	username_in_line = line.split('<', 1)[1].split('>', 1)[0]
	return username == username_in_line


def write_logout(username, curr_time, workdone) -> bool:
	"""
	I don't even want to know. This thing works, it's ok, don't touch it
	"""
	found = False

	log_list = []
	with open(LOG_FILENAME, "r") as log_file:
		for line in log_file:
			if inlab_line(line) and user_in_line(line, username):
				found = True
				login_time = line[12:17]
				logout_time = curr_time[11:17]
				line = line.replace("----------------", curr_time)
				line = line.replace("INLAB", work_time(login_time, logout_time))
				line = line.replace("\n", "")

				line = line + " :: " + workdone + "\n"
			log_list.append(line)  # Store everything in the list

	if found:
		# add .lock file during writing process if there isn't one, wait until it's removed, then re-add it
		while True:
			try:
				with open(LOG_FILENAME+'.lock', 'x'):
					break
			except FileExistsError:
				sleep(.5)

		# Writing everything to log file
		with open(LOG_FILENAME, "w") as log_file:
			for line in log_list:
				log_file.write(line)

		# remove .lock file
		os.remove(LOG_FILENAME+'.lock')

		# store_log_to(LOG_FILENAME, BACKUP_PATH)

	return found


# logout by passing manually date and time
def manual_logout():
	sys.stdout.write(COLOR_RED)
	username = input("ADMIN--> insert username: ")

	date = input("ADMIN--> insert date (gg/mm/aaaa): ")
	if not check_date(date):
		return False

	hour = input("ADMIN--> insert time (hh:mm): ")
	if not check_hour(hour):
		return False

	curr_time = date + " " + hour

	workdone = ask_work_done()

	print("ADMIN--> you will update the log file with ")
	print("            " + username + " " + curr_time)
	answer = input("ADMIN--> are you sure? (y/n)")
	if answer != "y":
		return False

	if write_logout(username, curr_time, workdone):
		print("ADMIN--> Update succeeded")
	else:
		print("ADMIN--> Update failed (not logged in?)")


def logfile():
	print(f"Reading log file...\n")
	with open(LOG_FILENAME, "r") as log_file:
		for line in log_file:
			print(line, end='')


def inlab():
	count = 0
	print(f"Reading log file...\n")
	with open(LOG_FILENAME, "r") as log_file:
		for line in log_file:
			if inlab_line(line):
				count += 1
				username = line[47:line.rfind(">")]
				print("> " + username)

	if count == 0:
		print(f"Nobody is in lab right now.")
	elif count == 1:
		print(f"There is one student in lab right now.")
	else:
		print(f"There are {count} students in lab right now.")


# Returns total work time in minutes
def tot_work_time(username):
	time_spent = 0
	with open(LOG_FILENAME, "r") as log_file:
		for line in log_file:
			if user_in_line(username, line) and not inlab_line(line):
				time_spent += ((int(line[39:41]) * 60) + int(line[42:44]))
	return time_spent


# Convert minutes in a formatted string
def time_conv(minutes):
	return str(int(minutes / 60)) + " h " + str(int(minutes % 60)) + " m"


def interactive_log(in_: bool, use_ldap: bool):
	retry = True
	retry_username = None
	while retry:
		try:
			if retry_username:
				username = retry_username
				retry_username = None
			else:
				username = input("Type your name.surname OR id (matricola) OR nickname OR swipe the card on the reader:\n")
				matricola_scan = read_from_card_reader(username)
				if matricola_scan:  # Input with magnetic card
					username = matricola_scan

			try:
				if in_:
					login(username, use_ldap)
					return True
				else:
					res = logout(username, use_ldap)
					if res:
						return True
			except LdapError:
				retry_ldap_question = True
				print(f"Hmmm... It seems the network or the LDAP server has some problems.")
				while retry_ldap_question:
					choice = input("Type R to retry or D to disable LDAP lookup: [R/D] ")
					choice = choice.strip().upper()
					if choice == 'R':
						retry_username = username
						retry_ldap_question = False
					elif choice == 'D':
						use_ldap = False
						retry_ldap_question = False
			except UserNotFoundError:
				pass
		except KeyboardInterrupt:
			print(f"Keyboard interrupt detected, interactive log{'in' if in_ else 'out'} cancelled")
			return False
		except EOFError:
			print(f"EOF detected, interactive log{'in' if in_ else 'out'} cancelled")
			return False


def read_from_card_reader(text: str) -> Optional[str]:
	old_format = False
	direction = None
	# matricola = None
	if text[0] == "ò":
		if text[-1] == "-":
			direction = " from top to bottom"
			old_format = True
		elif text[-1] == "_":
			direction = " from bottom to top"
			old_format = True
	elif text[0] == ";":
		if text[-1] == "/":
			direction = " from top to bottom"
			old_format = True
		elif text[-1] == "?":
			direction = " from bottom to top"
			old_format = True

	if old_format:
		matricola = text[9:15]
	else:
		matricola = read_from_card_reader_o_accentata(text, "ò")
		if not matricola:
			matricola = read_from_card_reader_o_accentata(text, ";")

	if matricola is not None:
		print(f"Detected card scan{direction if direction else ''} with matricola {matricola}")
		return matricola
	return None


def read_from_card_reader_o_accentata(text: str, delimiter: str):
	try:
		i = 0
		while 1:
			i = text.index(delimiter, i)
			if text[i + 1:i + 5] == "0000" and len(text) > i + 15 + 1:
				return text[i + 9:i + 15]
	except ValueError:
		return None



