#!/usr/bin/env python

"""
    Porthole
    A graphical frontend to Portage

    Copyright (C) 2003 - 2009 Fredrik Arnerup and Daniel G. Taylor,
    Brian Dolbec, William F. Wheeler, Brian Bockelman, Tommy Iorns

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""
import datetime
_id = datetime.datetime.now().microsecond
#print "STARTUP: id initialized to ", _id

import gi; gi.require_version("Gtk", "3.0") # make sure we have the right version
# proper way to enable threading.  Do this first before any other code
from gi.repository import GObject
GObject.threads_init()

from gi.repository import Gtk
from gi.repository import GdkPixbuf

import os
import sys


# Load EPREFIX from Portage, fall back to the empty string if it fails
try:
    from portage.const import EPREFIX
except ImportError:
    EPREFIX=''

# Add path to portage module if
# missing from path (ref bug # 924100)
PORTAGE_MOD_PATH = EPREFIX + '/usr/lib/portage/pym'
if PORTAGE_MOD_PATH not in sys.path:
    sys.path.append(PORTAGE_MOD_PATH)
#~ GENTOOLKIT_PATH = '/usr/lib/gentoolkit/pym'
#~ if GENTOOLKIT_PATH not in sys.path:
    #~ sys.path.append(GENTOOLKIT_PATH)

#while '' in sys.path: # we don't need the cwd in the path
#    sys.path.remove('')
while EPREFIX + '/usr/bin' in sys.path: # this gets added when we run /usr/bin/porthole
    sys.path.remove(EPREFIX + '/usr/bin')

APP = 'porthole'
LOG_FILE_DIR = EPREFIX + "/var/log/porthole"
DB_FILE_DIR = EPREFIX + "/var/db/porthole"
Choices = {"portage": 'portagelib', "pkgcore": 'pkgcore_lib', "dbus": "dbus_main"}
BACKEND = Choices["portage"]
DATA_PATH = EPREFIX + "/usr/share/porthole/"
i18n_DIR = DATA_PATH + 'i18n'
RUN_LOCAL = False
DIR_LIST = [LOG_FILE_DIR, DB_FILE_DIR]


#from thread import *
import gi; gi.require_version("Gtk", "3.0") # make sure we have the right version
while EPREFIX + '/usr/bin' in sys.path: # and now importing gtk re-adds it! Grrrr, rude
    sys.path.remove(EPREFIX + '/usr/bin')
import locale
import gettext


def create_dir(new_dir):
    """Creates the directory passed into it"""
    print("STARTUP: create_dir; ", new_dir + " does not exist, creating...")
    try:
        os.mkdir(new_dir)
    except OSError as e:
        errnum, errmsg = e.args
        print("Failed to create %s:" % new_dir, errmsg)


def import_error(e):
    print("*** Error loading porthole modules!\n*** If you are running a",
          "local (not installed in python's site-packages) version, please use the '--local'",
          "or '-l' flag.\n",
          "*** Otherwise, verify that porthole was installed correctly and",
          "that python's path includes the site-packages directory.\n",
          "If you have recently updated python, then run 'python-updater'\n")
    print("Your sys.path: %s\n" % sys.path)
    print("Your sys.version: %s\n" % sys.version)
    print("Original exception was: ImportError: %s\n" % e)
    sys.exit()

def local():
    global DATA_PATH, i18n_DIR, RUN_LOCAL
    # if opt in ("-l", "--local"):
    # running a local version (i.e. not installed in /usr/*)
    #print "STARTUP: local(); setting to local paths"
    DATA_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+"/porthole/"
    #DATA_PATH = getcwd() + "/"
    i18n_DIR = DATA_PATH + 'i18n'
    RUN_LOCAL = True

location = os.path.abspath(__file__)
if "site-packages" not in location:
    local()


def set_debug(arg):
    from porthole.utils import debug
    debug.set_debug(True)
    #print "Debug printing is enabled = ", debug.debug, "; debug.id = ", debug.id
    debug.debug_target = arg
    #print("Debug print filter set to ", debug.debug_target)

def print_version():
    # print version info
    from porthole.version import version
    print("Porthole ", version)
    sys.exit(0)

def usage():
    """Display basic command line help"""
    tabs = "\t\t"
    print("Usage: porthole [OPTION...]\n")
    print("  -h, --help" + tabs + "Show this help message")
    print("  -l, --local" + tabs +
          "Run a local version (use modules in current directory)")
    print("  -v, --version" + tabs + "Output version information and exit")
    print("  -d, --debug string" + tabs +
          "Output debugging information to stderr")
    print("  -b, --backend [portage, pkgcore]" + tabs + "Select backend")

def set_backend(arg):
    if arg in Choices:
        global BACKEND
        # fixme unused BACKEND
        BACKEND = Choices[arg]
        print("***** BACKEND set to:", BACKEND)
    else:
        usage()

def insert_path():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    #print(sys.path)


def main():
    """start the porthole frontend"""
    try:
        #print "STARTUP: main(); thread id = ", thread.get_ident()
        #print "STARTUP: main(); importing config"
        from porthole import config
        #print "STARTUP: config.id = ", config.id
        #print "STARTUP: main(); importing config.preferences"
        from porthole.config import preferences
    except ImportError as e:
        import_error(e)
    # load prefs
    prefs_additions = [
        ["DATA_PATH",DATA_PATH],
        ["APP",APP],
        ["i18n_DIR",i18n_DIR],
        ["RUN_LOCAL",RUN_LOCAL],
        ["LOG_FILE_DIR",LOG_FILE_DIR],
        ["PORTAGE", BACKEND],
        ["EPREFIX", EPREFIX]
    ]
    #print "STARTUP: main(); loading preferences"
    config.Prefs = preferences.PortholePreferences(prefs_additions)
    #print config.Prefs
    #print "STARTUP: main(); importing utils"
    from porthole.utils import debug
    from porthole import backends
    from porthole.backends import load
    load(BACKEND)
    print("PORTHOLE: importing MainWindow")
    from porthole.mainwindow import MainWindow

    print("PORTHOLE: i18n_DIR =" + str(i18n_DIR))
    locale.setlocale (locale.LC_ALL, '')
    gettext.bindtextdomain (APP, i18n_DIR)
    gettext.textdomain (APP)
    gettext.install (APP, i18n_DIR)
    # builder = gtk.Builder()
    # builder.set_translation_domain(APP)
    #Gtk.glade.bindtextdomain (APP, i18n_DIR)
    #Gtk.glade.textdomain (APP)

    # make sure gtk lets threads run
    #os.putenv("PYGTK_USE_GIL_STATE_API", "True")
    #Gtk.threads_init()

    debug.dprint("PORTHOLE: process id = %d ****************" %os.getpid())
    # setup our app icon
    myicon = GdkPixbuf.Pixbuf.new_from_file(DATA_PATH + "pixmaps/porthole-icon.png")
    Gtk.Window.set_default_icon_list([myicon])
    # load config info
    config.Config.set_path(DATA_PATH)
    config.Config.load()
    config.Prefs.use_gladefile = "not assigned"
    # create the main window
    MainWindow() #config.Prefs, config.Config)
    # start the program loop
    Gtk.main()
    # save the prefs to disk for next time
    config.Prefs.save()
    print("metadata", backends.portage_lib.get_metadata.cache_info())
    sys.exit(0)

# check if directory exists, if not create it
for _dir in DIR_LIST:
    if not os.access(_dir, os.F_OK):
        create_dir(_dir)
