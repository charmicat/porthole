#!/usr/bin/env python3

from setuptools import setup, find_packages  # or find_namespace_packages
from porthole.version import version as p_version

datadir = "share/porthole/"

setup(
    name = "porthole",
    version='0.0.1',
    description = "GTK+ frontend to Portage",
    author = "Fredrik Arnerup, Daniel G. Taylor, Brian Dolbec, William F. Wheeler",
    author_email = "dol-sen@users.sourceforge.net, "
                   "farnerup@users.sourceforge.net, dgt84@users.sourceforge.net, "
                   " tiredoldcoder@users.sourceforge.net",
    url = "https://porthole.sourceforge.net",
    build_requires=["requirements","setuptools"],

    install_requires=["requirements","setuptools"],
    packages=find_packages(
    # All keyword arguments below are optional:
        where='.',  # '.' by default
        include=['porthole*'],  # ['*'] by default
    ),
    # packages = ['porthole',  'porthole.advancedemerge', 'porthole.backends', 'porthole.config',
    #                     'porthole.db', 'porthole.dialogs', 'porthole.loaders', 'porthole.mwsupport',
    #                     'porthole.plugins','porthole.loaders', 'porthole.readers', 'porthole.terminal',
    #                     'porthole.utils', 'porthole.views', 'porthole._xml', 'porthole.plugins.etc-proposals',
    #                     'porthole.plugins.gpytage',
    #                     'porthole.views.packagebook'],
    package_dir = {'porthole':'porthole'},
    scripts = ["scripts/porthole"],
    data_files = [
        (datadir + "pixmaps",
            ["porthole/pixmaps/porthole-about.png", "porthole/pixmaps/porthole-icon.png", 
            "porthole/pixmaps/porthole-clock-20x20.png", "porthole/pixmaps/porthole-clock.png",
            "porthole/pixmaps/porthole.svg"]),
        (datadir + "help",
            ["porthole/help/advemerge.html", "porthole/help/advemerge.png", "porthole/help/changelog.png",
            "porthole/help/custcmd.html", "porthole/help/custcmd.png", "porthole/help/customize.html",
            "porthole/help/dependencies.png", "porthole/help/index.html", "porthole/help/install.html",
            "porthole/help/installedfiles.png", "porthole/help/mainwindow.html", "porthole/help/mainwindow.png",
            "porthole/help/porthole.css", "porthole/help/queuetab.png", "porthole/help/search.html",
            "porthole/help/summarytab.png", "porthole/help/sync.html", "porthole/help/termrefs.html",
            "porthole/help/termwindow.html", "porthole/help/termwindow.png", "porthole/help/toc.html",
            "porthole/help/unmerge.html", "porthole/help/update.html", "porthole/help/warningtab.png",
            "porthole/help/depview.png", "porthole/help/ebuildtable_explained2.png", 
            "porthole/help/upgradeables.png"]),
        (datadir + "glade",
            ["porthole/glade/config.ui", "porthole/glade/advemerge.ui",
            "porthole/glade/porthole.ui", "porthole/glade/about.ui"]),
        (datadir,
            ["scripts/dopot.sh", "scripts/pocompile.sh", "AUTHORS"]),
        (datadir + "config",
            [ "porthole/config/configuration.xml"]),
        (datadir + "i18n",
            ["porthole/i18n/messages.pot", "porthole/i18n/TRANSLATING"]),
        ("share/applications", ["porthole.desktop"]),
        ("share/pixmaps", ["porthole/pixmaps/porthole-icon.png"])
    ]
)
