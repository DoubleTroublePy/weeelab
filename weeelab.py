#!/usr/bin/env python3

"""
WEEELAB - Log management module for garbaging paper sign sheet.
Author: Hyd3L

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import argparse
# For the copyright string in --help
from argparse import RawDescriptionHelpFormatter
from shutil import copy2
# Allows using backspace and arrow keys in input
# noinspection PyUnresolvedReferences
import readline
from datetime import datetime
from time import sleep
from select import select
import subprocess
import os

if '--no-ldap' not in sys.argv:
	from ldap.filter import escape_filter_chars
	import ldap


# import locals
from constans import *


def main(args_dict):
	# root execution check
	if os.geteuid() == 0:
		print("Error: can't execute " + PROGRAM_NAME + " as root.")
		exit(42)

	if args_dict.get('debug'):
		global DEBUG_MODE
		DEBUG_MODE = True
		print(f"DEBUG_MODE enabled")
		global LOG_FILENAME
		LOG_FILENAME = "./debug/log.txt"

	ensure_log_file()
	create_backup_if_necessary()

	result = True
	interactive = False
	try:
		if args_dict.get('login'):
			login(args_dict.get('login')[0], args_dict.get('ldap'))
		elif args_dict.get('logout'):
			if args_dict.get('message') is None:
				message = None
			else:
				message = args_dict.get('message')[0]
			result = logout(args_dict.get('logout')[0], args_dict.get('ldap'), message)
		elif args_dict.get('interactive_login'):
			interactive = True
			result = interactive_log(True, args_dict.get('ldap'))
		elif args_dict.get('interactive_logout'):
			interactive = True
			result = interactive_log(False, args_dict.get('ldap'))
		elif args_dict.get('inlab'):
			inlab()
		elif args_dict.get('log'):
			logfile()
		elif args_dict.get('admin'):
			result = manual_logout()
		else:
			print("WTF?")
			exit(69)
	except LdapError:
		result = False
	except UserNotFoundError:
		result = False

	auto_close = True

	if SIR_HAPPENED:
		red = "\033[41m\033[30m"
		yellow = "\033[41m\033[97m"
		border = "\033[103m"
		bold = ""  # "\033[1m"
		disagio = "\033[5m"
		# underline = "\033[4m"
		underline = "\033[97m"
		reset = "\033[0m"
		# print("\x1b[1;37;44m")
		# print("\x1b[1;34;41m")
        
        # 74 spaces
		print(f"{red}{bold}")
		print(f"                                                                          ")
		print(f"                                                                          ")
		print(f"                                 {border}                   {red}")
		print(f"                                 {border}  {red}               {border}  {red}")
		print(f"                                 {border}  {yellow}{disagio} SIGN THE SIR!{reset}{red} {border}  {red}")
		print(f"                                 {border}  {red}               {border}  {red}")
		print(f"                                 {border}                   {red}")
		print(f"")
		print(f" This is mandatory and very important, you have to make {underline}4 signatures{reset}{red} on a boring form.")
		print(f"              Ask someone else in lab or on Telegram to provide you the form.")
		print(f"")
		# print("\x1b[1;37;44m")
		print(reset)
		auto_close = False

	if FIRST_IN_HAPPENED:
		if FIRST_IN:
			if os.path.isfile(FIRST_IN):
				print("I'm now launching the \"first in\" script, but you can close this window")
				subprocess.Popen([FIRST_IN])
			else:
				print(f"The \"first in\" script \"{FIRST_IN}\" does not exist, notify an administrator")

	if LAST_OUT_HAPPENED:
		if LAST_OUT:
			if os.path.isfile(LAST_OUT):
				print("I'm now launching the \"last out\" script, but you can close this window")
				subprocess.Popen([LAST_OUT])
			else:
				print(f"The \"last out\" script \"{LAST_OUT}\" does not exist, notify an administrator")

	if interactive:
		if auto_close and result:
			print("Press enter to exit (or wait 10 seconds)")
			# does not work on windows:
			select([sys.stdin], [], [], 10)
		else:
			print("Press enter to exit")
			# does not work on windows:
			input()

	if not result:
		secure_exit(3)


def argparse_this():
	parser = argparse.ArgumentParser(formatter_class=RawDescriptionHelpFormatter, description="""
WEEELAB v{} - Log management module for garbaging paper sign sheet.
Author: Stefano Enrico Mendola (aka Hyd3L, STE col teschio) and others
Copyright (C) 2017-∞ WEEE Open

This program comes with ABSOLUTELY NO WARRANTY.
Since this is a free software, you are welcome
to redistribute it under the terms of the GNU GPLv3.
	""".format(VERSION))
	# Add commands here, like any normal person instead of hand-coding a parser (or at least make it a LALR(1) parser)
	parser.add_argument('-d', '--debug', action='store_true', help='enable debug mode (don\'t copy files to ownCloud)')
	group = parser.add_argument_group('Actions').add_mutually_exclusive_group(required=True)
	group.add_argument('-i', '--login', type=str, nargs=1, metavar='USER', help='log in USER')
	group.add_argument('-o', '--logout', type=str, nargs=1, metavar='USER', help='log out USER')
	group.add_argument('--interactive-login', action='store_true', help='log in with questions')
	group.add_argument('--interactive-logout', action='store_true', help='log out with questions')
	parser.add_argument('-m', '--message', type=str, nargs=1, metavar='MESSAGE', help='logout message')
	group.add_argument('-p', '--inlab', action='store_true', help='show who\'s in lab (logged in)')
	group.add_argument('-l', '--log', action='store_true', help='show log file')
	group.add_argument('-a', '--admin', action='store_true', help='enter admin mode')
	ldap_group_argparse_thing = parser.add_mutually_exclusive_group(required=False)
	ldap_group_argparse_thing.add_argument('--ldap', dest='ldap', action='store_true')
	ldap_group_argparse_thing.add_argument('--no-ldap', dest='ldap', action='store_false')
	ldap_group_argparse_thing.set_defaults(ldap=True)
	args = parser.parse_args()
	if args.message is not None and args.logout is None:
		parser.error("You can't set a logout message alone or for other commands other than logout.\n"
					 "You can use -m or its equivalent --message only if you also use the -o or --logout parameter.")
	return args


if __name__ == '__main__':
	main(vars(argparse_this()))
