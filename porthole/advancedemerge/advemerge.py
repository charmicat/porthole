#!/usr/bin/env python

"""
    Porthole Advanced Emerge Dialog
    Allows the user to set options, use flags, keywords and select
    specific versions.  Has lots of tool tips, too.

    Copyright (C) 2003 - 2011 Fredrik Arnerup, Daniel G. Taylor, Brian Dolbec,
    Wm. F. Wheeler and Tommy Iorns

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
print("ADVEMERGE: id initialized to ", _id)

# import gtk & co
from gi.repository import Gtk
#from gi.repository import Gladeui

from gettext import gettext as _


from porthole.utils import utils
from porthole.utils import debug
from porthole import config
from porthole import backends
from porthole import db
from porthole.backends.version_sort import ver_sort
from porthole.backends.utilities import (
    abs_list,
    filter_flags
)
from porthole.loaders.loaders import load_web_page
from porthole.utils.dispatcher import Dispatcher
from porthole.views.useflags import UseFlagWidget

class AdvancedEmergeDialog:
    """Class to perform advanced emerge dialog functionality."""

    def __init__(self, package, setup_command, re_init_portage):
        """ Initialize Advanced Emerge Dialog window """
        # Preserve passed parameters
        self.package = package
        self.setup_command = setup_command
        self.re_init_portage = re_init_portage
        self.arch = backends.portage_lib.get_arch()
        self.system_use_flags = backends.portage_lib.settings.SystemUseFlags
        self.emerge_unmerge = "emerge"
        self.is_root = utils.is_root()
        self.package_use_flags = db.userconfigs.get_user_config('USE', package.full_name)
        self.current_verInfo = None

        # Parse glade file
        self.gladefile = config.Prefs.DATA_PATH + "glade/advemerge.glade"
        self.wtree = Gtk.Builder()
        self.wtree.add_from_file(self.gladefile)
        self.wtree.set_translation_domain(config.Prefs.APP)

        # register callbacks
        callbacks = {"on_ok_clicked" : self.ok_clicked,
                     "on_help_clicked" : self.help_clicked,
                     "on_cancel_clicked" : self.cancel_clicked,
                     #"on_cbAsk_clicked": self.Ask_clicked,
                     "on_cbOnlyDeps_clicked" : (self.set_one_of, 'cbOnlyDeps', 'cbNoDeps'),
                     "on_cbNoDeps_clicked" : (self.set_one_of, 'cbNoDeps', 'cbOnlyDeps'),
                     "on_cbQuiet_clicked" : (self.set_one_of, 'cbQuiet', 'cbVerbose'),
                     "on_cbVerbose_clicked" : (self.set_one_of, 'cbVerbose', 'cbQuiet'),
                     "on_cbBuildPkg_clicked" : (self.set_one_of, 'cbBuildPkg', 'cbBuildPkgOnly'),
                     "on_cbBuildPkgOnly_clicked" : (self.set_one_of, 'cbBuildPkgOnly', 'cbBuildPkg'),
                     "on_cbUsePkg_clicked" : (self.set_one_of, 'cbUsePkg', 'cbUsePkgOnly'),
                     "on_cbUsePkgOnly_clicked" : (self.set_one_of, 'cbUsePkgOnly', 'cbUsePkg'),
                     "on_cmbVersion_changed" : self.version_changed,
                     "on_cmbEmerge_changed" : self.emerge_changed,
                     "on_btnPkgUse_clicked" : self.on_package_use_commit,
                     "on_btnMakeConf_clicked" : self.on_make_conf_commit,
                     "on_btnPkgKeywords_clicked" : self.on_package_keywords_commit,
                     "on_cbColorY_clicked": (self.set_one_of, 'cbColorY', 'cbColorN'),
                     "on_cbColorN_clicked": (self.set_one_of, 'cbColorN', 'cbColorY'),
                     "on_cbColumns_clicked": (self.set_all, 'cbColumns','cbPretend'),
                     'on_cbWithBDepsY_clicked': (self.set_one_of, 'cbWithBDepsY', 'cbWithBDepsN'),
                     'on_cbWithBDepsN_clicked': (self.set_one_of, 'cbWithBDepsN', 'cbWithBDepsY'),
                     'on_cbGetBinPkg_clicked': (self.set_one_of, 'cbGetBinPkg', 'cbGetBinPkgOnly'),
                     'on_cbGetBinPkgOnly_clicked': (self.set_one_of, 'cbGetBinPkgOnly', 'cbGetBinPkg' ),
                     "on_toggled": self.on_toggled
        }

        self.wtree.connect_signals(callbacks)
        self.window = self.wtree.get_object("adv_emerge_dialog")
        self.use_flags_frame = self.wtree.get_object("frameUseFlags")
        self.keywords_frame = self.wtree.get_object("frameKeywords")
        self.window.set_title(_("Advanced Emerge Settings for %s") % package.full_name)

        self.command_textview = self.wtree.get_object("command_textview")
        self.command_buffer = self.command_textview.get_buffer()
        style = self.keywords_frame.get_style().copy()
# Fixme needs porting ???
# <<<<<<< ours
        # #self.bgcolor = style.bg[Gtk.StateType.NORMAL]
        # self.bgcolor = style.bg[Gladeui.PropertyState.NORMAL]
        # #self.command_textview.modify_base(Gtk.StateType.NORMAL, self.bgcolor)
        # self.command_textview.modify_base(Gladeui.PropertyState.NORMAL, self.bgcolor)

# =======
        # self.bgcolor = style.bg[Gladeui.PropertyState.NORMAL]
        # self.command_textview.modify_base(Gladeui.PropertyState.NORMAL, self.bgcolor)

# >>>>>>> theirs
        self.btnMakeConf = self.wtree.get_object("btnMakeConf")
        self.btnPkgUse = self.wtree.get_object("btnPkgUse")
        self.btnPkgKeywords = self.wtree.get_object("btnPkgKeywords")
        if not self.is_root and not utils.can_gksu():
            debug.dprint("ADVEMERGE: self.is_root = %s, utils.can_gksu = %s" %(self.is_root, utils.can_gksu))
            self.btnMakeConf.hide()
            self.btnPkgUse.hide()
            self.btnPkgKeywords.hide()

        # Connect option toggles to on_toggled
        for checkbutton in self.wtree.get_object("table2").get_children():
            if isinstance(checkbutton, Gtk.CheckButton):
                checkbutton.connect("toggled", self.on_toggled)
            #else:
            #    debug.dprint("ADVEMERGE: table2 has child not of type Gtk.CheckButton")
            #    debug.dprint(checkbutton)

        if not config.Prefs.advemerge.showuseflags:
            self.use_flags_frame.hide()
        if not config.Prefs.advemerge.showkeywords:
            self.keywords_frame.hide()

        # Make tool tips available
        #self.tooltips = Gtk.Tooltips()

        # Build version combo list
        self.get_versions()

        # Build a formatted combo list from the versioninfo list
        self.comboList = Gtk.ListStore(str)
        index = 0
        for x in range(len(self.verList)):
            ver = self.verList[x]
            info = ver["number"]
            slot = ver["slot"]
            if slot != '0':
                info += ''.join(['   [', _('Slot:%s') % slot, ']'])
            if not ver["available"]:
                info += _('   {unavailable}')
            elif not ver["stable"]:
                info += _('   (unstable)')
            if ver["hard_masked"]:
                info += _('   [MASKED]')
            if ver["best"]:
                if ver["best_downgrades"]:
                    info += _('   (recommended) (downgrade)')
                else:
                    info += _('   (recommended)')
                index = x
            if ver["installed"]:
                info += _('   [installed]')

            self.comboList.append([info])

        # Build version combobox
        self.combobox = self.wtree.get_object("cmbVersion")
        self.combobox.set_model(self.comboList)
        cell = Gtk.CellRendererText()
        self.combobox.pack_start(cell, True)
        self.combobox.add_attribute(cell, 'text', 0)
        self.combobox.set_active(index) # select "recommended" ebuild by default

        # emerge / unmerge combobox:
        self.emerge_combolist = Gtk.ListStore(str)
        _iter = self.emerge_combolist.append(["emerge"])
        self.emerge_combolist.append(["unmerge"])
        self.emerge_combobox = self.wtree.get_object("cmbEmerge")
        self.emerge_combobox.set_model(self.emerge_combolist)
        cell = Gtk.CellRendererText()
        self.emerge_combobox.pack_start(cell, True)
        self.emerge_combobox.add_attribute(cell, 'text', 0)
        self.emerge_combobox.set_active_iter(_iter)

        # Set any emerge options the user wants defaulted
        if config.Prefs.emerge.pretend:
            self.wtree.get_object("cbPretend").set_active(True)
        if config.Prefs.emerge.verbose:
            self.wtree.get_object("cbVerbose").set_active(True)
        ## this now just references --update, which is probably not the desired behaviour.
        ## perhaps the current version should be indicated somewhere in the dialog
        #if config.Prefs.emerge.upgradeonly:
        #    self.wtree.get_object("cbUpgradeOnly").set_active(True)
        if config.Prefs.emerge.fetch:
            self.wtree.get_object("cbFetchOnly").set_active(True)
        if config.Prefs.emerge.nospinner:
            self.wtree.get_object("cbNoSpinner").set_active(True)

        # show command in command_label
        self.display_emerge_command()

    #-----------------------------------------------
    # GUI Callback function definitions start here
    #-----------------------------------------------

    def ok_clicked(self, widget):
        """ Interrogate object for settings and start the ebuild """
        command = self.get_command()

        # Dispose of the dialog
        self.window.destroy()

        # Submit the command for processing
        self.setup_command(self.package.get_name(), command)

    def cancel_clicked(self, widget):
        """ Cancel emerge """
        self.window.destroy()


    def help_clicked(self, widget):
        """ Display help file with web browser """
        load_web_page('file://' + config.Prefs.DATA_PATH + 'help/advemerge.html', config.Prefs)

    def version_changed(self, widget):
        """ Version has changed, update the dialog window """
        debug.dprint("ADVEMERGE: changing version")
        _iter = self.combobox.get_active_iter()
        model = self.combobox.get_model()
        sel_ver = model.get_value(_iter, 0)
        if len(sel_ver) > 2:
            verInfo = self.current_verInfo = self.get_verInfo(sel_ver)
            # Reset use flags
            self.build_use_flag_widget(verInfo["use_flags"], verInfo["name"])
            # Reset keywords
            self.build_keywords_widget(verInfo["keywords"])
        self.display_emerge_command()

    def emerge_changed(self, widget):
        """ Swap between emerge and unmerge """
        debug.dprint("ADVEMERGE: emerge_changed()")
        _iter = self.emerge_combobox.get_active_iter()
        model = self.emerge_combobox.get_model()
        self.emerge_unmerge = model.get_value(_iter, 0)
        self.display_emerge_command()

    def set_all(self, widget, *args):
        if widget.get_active():
            for x in args:
                self.wtree.get_object(x).set_active(True)
            return False

    def set_one_of(self, widget, *args):
        if widget.get_active():
            self.wtree.get_object(args[0]).set_active(True)
            for x in args[1:]:
                self.wtree.get_object(x).set_active(False)
            return False

    def on_toggled(self, widget):
        self.display_emerge_command()
        return False

    def on_package_use_commit(self, button_widget):
        debug.dprint("ADVEMERGE: on_package_use_commit()")
        use_flags = self.get_use_flags()
        if not use_flags: return
        addlist = use_flags.split()
        removelist = []
        for item in addlist: # get opposite of flags
            if item.startswith('-'):
                removelist.append(item[1:])
            else:
                removelist.append('-' + item)
        addlist = [item[1:] if item.startswith('+') else item for item in addlist]
        #debug.dprint("ADVEMERGE: on_package_use_commit(); addlist:%s,\n removelist:%s" %(str(addlist), str(removelist)))
        # fixme okay not used
        okay = db.userconfigs.set_user_config('USE', name=self.package.full_name, add=addlist,
                                                                remove=removelist, callback=self.reload, parent_window = self.window )
        self.version_changed(button_widget)

    def on_make_conf_commit(self, button_widget):
        debug.dprint("ADVEMERGE: on_make_conf_commit()")
        use_flags = self.get_use_flags()
        if not use_flags: return
        addlist = use_flags.split()
        removelist = []
        for item in addlist: # get opposite of flags
            if item.startswith('-'):
                removelist.append(item[1:])
            else:
                removelist.append('-' + item)
        # set_user_config must be performed after set_make_conf has finished or we get problems.
        # we need to set package.use in case the flag was set there originally!
        package_use_callback = Dispatcher( db.userconfigs.set_user_config,
                                           'USE', self.package.full_name, '', '', removelist, self.reload )
        backends.portage_lib.set_make_conf('USE', add=addlist, remove=removelist, callback=package_use_callback )
        self.version_changed(button_widget)

    def on_package_keywords_commit(self, button_widget):
        debug.dprint("ADVEMERGE: on_package_keywords_commit()")
        keyword = self.get_keyword()
        if not keyword: return
        addlist = [keyword]
        if keyword.startswith("-"):
            removelist = [keyword[1:]]
        else:
            removelist = ["-" + keyword]
        verInfo = self.current_verInfo
        ebuild = verInfo["name"]
        # fixme okay not used
        okay = db.userconfigs.set_user_config('KEYWORDS', ebuild=ebuild, add=addlist, remove=removelist, callback=self.reload)

    #------------------------------------------
    # Support function definitions start here
    #------------------------------------------

    def reload(self):
        """ Reload package info """
        # This is the callback for changes to portage config files, so we need to reload portage
        ## now done elsewhere
        ##self.re_init_portage()

        # Also delete properties for the current ebuild so they are refreshed
        verInfo = self.current_verInfo
        ebuild = verInfo["name"]
        #~ if ebuild in self.package.properties:
            #~ # Remove properties object so everything's recalculated
            #~ del self.package.properties[ebuild]
        # Remove properties object so everything's recalculated
        self.package.properties.pop(ebuild, None)
        self.system_use_flags = backends.portage_lib.settings.SystemUseFlags
        self.package_use_flags = db.userconfigs.get_user_config('USE', self.package.full_name)
        #debug.dprint(self.package_use_flags)

        self.current_verInfo = None
        self.get_versions()

        oldindex = self.combobox.get_active()

        # Rebuild version liststore
        self.comboList = Gtk.ListStore(str)
        for x in range(len(self.verList)):
            ver = self.verList[x]
            info = ver["number"]
            slot = ver["slot"]
            if slot != '0':
                info += ''.join(['   [', _('Slot:%s') % slot, ']'])
            if not ver["available"]:
                info += _('   {unavailable}')
            elif not ver["stable"]:
                info += _('   (unstable)')
            if ver["hard_masked"]:
                info += _('   [MASKED]')
            if ver["best"]:
                if ver["best_downgrades"]:
                    info += _('   (recommended) (downgrade)')
                else:
                    info += _('   (recommended)')
            if ver["installed"]:
                info += _('   [installed]')

            self.comboList.append([info])

        self.combobox.set_model(self.comboList)
        self.combobox.set_active(oldindex)

        self.display_emerge_command()

    def get_versions(self):
        """ Build a dictionary of all versions for this package
            with an info list for each version

            info["number"] = version number only
            info["name"] = full ebuild name
            info["best"] = True if best version for this system
            info["best_downgrades"] = True if "best" version will downgrade
            info["installed"] = True if installed
            info["slot"] = slot number
            info["keywords"] = keyword list
            info["use_flags"] = use flag list
            info["stable"] = True if stable on current architecture
            info["hard_masked"] = True if hard masked
            info["available"] = False if the ebuild is no longer available
        """
        self.verList = []
        # Get all versions sorted in chronological order
        portage_versions = self.package.get_versions()

        # Get all installed versions
        installed = self.package.get_installed()

        ebuilds = portage_versions[:]
        for item in installed:
            if item not in portage_versions:
                ebuilds.append(item)

        ebuilds = ver_sort(ebuilds)

        # get lists of hard masked and stable versions (unstable inferred)
        hardmasked = self.package.get_hard_masked(check_unmask = True)
        nonmasked = self.package.get_versions(include_masked = False)

        # iterate through ebuild list and create data structure
        for ebuild in ebuilds:
            info = {}
            props = self.package.get_properties(ebuild)
            info["name"] = ebuild
            info["number"] = backends.portage_lib.get_version(ebuild)
            if ebuild == self.package.get_best_ebuild():
                info["best"] = True
                info["best_downgrades"] = ebuild not in backends.portage_lib.best(installed + [ebuild])
            else:
                info["best"] = info["best_downgrades"] = False
            info["installed"] = ebuild in installed
            info["slot"] = props.get_slot()
            info["keywords"] = props.get_keywords()
            iuse = props.get_use_flags()
            final_use, use_expand_hidden, usemasked, useforced = backends.portage_lib.get_cpv_use(ebuild)
            myflags = filter_flags(iuse, use_expand_hidden, usemasked, useforced)
            info["use_flags"] = abs_list(myflags)
            info["stable"] = ebuild in nonmasked
            info["hard_masked"] = ebuild in hardmasked
            info["available"] = ebuild in portage_versions
            self.verList.append(info)

    def get_verInfo(self, version):
        # Find selected version
        sel_ver = version.split(' ')[0]
        for x in range(len(self.verList)):
            ver = self.verList[x]
            if sel_ver == ver["number"]:
               verInfo = ver
               break
        if not verInfo:
            debug.dprint("ADVEMERGE: get_verInfo(); freaking out! what's \"verInfo\"?")
            verInfo = "?"
        return verInfo

    def get_keyword(self):
        """ Get keyword selected by user """
        keyword = ''
        for item in self.kwList:
            keyword = item[1]
            if item[0].get_active():
                verInfo = self.current_verInfo
                if keyword == None: # i.e. "None" is selected
                    # check to see if the ebuild is keyword unmasked,
                    if verInfo["stable"] and self.arch not in verInfo["keywords"]:
                        # i.e. "~arch" is in keywords, not "arch" => must be unmasked
                        # so: re-mask it (for use with package.keywords button)
                        return "-~" + self.arch
                    keyword = ''
                if verInfo["stable"] and keyword in backends.portage_lib.settings.settings["ACCEPT_KEYWORDS"]: return ''
                return keyword.strip()
        return ''

    def get_use_flags(self, ebuild=None):
        """ Get use flags selected by user """
        UseFlagsFrame = self.wtree.get_object('frameUseFlags')
        child = UseFlagsFrame.get_child()
        if child is None:
           return None
        else:
           return child.get_use_flags()

    def get_options(self):
        """ Create keyword list from option checkboxes """
        List = [('cbAlphabetical', '--alphabetical ', '--alphabetical '),
                ('cbAsk', '-a ', '--ask '),
                ('cbBuildPkg', '-b ', '--buildpkg '),
                ('cbBuildPkgOnly', '-B ', '--buildpkgonly '),
                ('cbColorY', '--color y ', '--color y ' ),
                ('cbColorN', '--color n ', '--color n ' ),
                ('cbDebug', '-d ', '--debug '),
                ('cbDeep', '-D ', '--deep '),
                ('cbEmptyTree', '-e ', '--emptytree '),
                ('cbFetchOnly', '-f ', '--fetchonly '),
                ('cbFetchAllUri', '-F ', '--fetch-all-uri '),
                ('cbGetBinPkg', '-g ', '--getbinpkg '),
                ('cbGetBinPkgOnly', '-G ', '--getbinpkgonly '),
                ('cbIgnoreDefaultOptions',  '--ignore-default-opts ', '--ignore-default-opts '),
                ('cbNewUse', '-N ', '--newuse '),
                ('cbNoConfMem', '--noconfmem ', '--noconfmem '),
                ('cbNoDeps', '-O ', '--nodeps '),
                ('cbNoReplace', '-n ', '--noreplace '),
                ('cbNoSpinner', '--nospinner ', '--nospinner '),
                ('cbOneShot', '--oneshot ', '--oneshot '),
                ('cbOnlyDeps', '-o ', '--onlydeps '),
                ('cbPretend','-p ', '--pretend '),
                ('cbColumns', '--columns ', '--columns '),
                ('cbQuiet', '-q ', '--quiet '),
                ('cbTree', '-t ', '--tree '),
                ('cbUpdate','-u ', '--update '),
                ('cbUsePkg', '-k ', '--usepkg '),
                ('cbUsePkgOnly', '-K ', '--usepkgonly '),
                ('cbVerbose', '-v ', '--verbose '),
                ('cbWithBDepsY', '--with-bdeps y ', '--with-bdeps y '),
                ('cbWithBDepsN', '--with-bdeps n ', '--with-bdeps n ')
                ]
        options = ''
        for Name, ShortOption, LongOption in List:
            if self.wtree.get_object(Name) and self.wtree.get_object(Name).get_active():
                options += LongOption
        #if config.Prefs.emerge.nospinner:
        #    options += '--nospinner '
        return options

    def get_command(self):
        # Get selected version from combo list
        _iter = self.combobox.get_active_iter()
        model = self.combobox.get_model()
        sel_ver = model.get_value(_iter, 0)

        # Get version info of selected version
        verInfo = self.get_verInfo(sel_ver)

        # Build use flag string
        use_flags = self.get_use_flags(verInfo["name"])
        if len(use_flags) > 0:
            use_flags = 'USE="' + use_flags + '" '
            self.btnPkgUse.set_sensitive(True)
            self.btnMakeConf.set_sensitive(True)
        else:
            self.btnPkgUse.set_sensitive(False)
            self.btnMakeConf.set_sensitive(False)

        # Build accept keyword string
        accept_keyword = self.get_keyword()
        if len(accept_keyword) > 0:
            accept_keyword = "ACCEPT_KEYWORDS='" + accept_keyword + "' "
            self.btnPkgKeywords.set_sensitive(True)
        else:
            self.btnPkgKeywords.set_sensitive(False)

        # Build emerge or unmerge base command
        if self.is_root or self.wtree.get_object("cbPretend").get_active():
            emerge_unmerge = ''
        else:
            emerge_unmerge = 'sudo -p "Password: " '

        if self.emerge_unmerge == "emerge":
            emerge_unmerge += "emerge "
        else: # self.emerge_unmerge == "unmerge"
            emerge_unmerge += "emerge --unmerge "

        # Send command to be processed
        command = ''.join([
            use_flags,
            # accept_keyword, # this sole 'feature' has caused so many times emerging unstable code.
            emerge_unmerge,
            self.get_options(),
            '=',
            verInfo["name"]
        ])
        return command

    def display_emerge_command(self):
        command = self.get_command()
        end = self.command_buffer.get_end_iter()
        start = self.command_buffer.get_start_iter()
        self.command_buffer.delete(start, end)
        self.command_buffer.insert(self.command_buffer.get_end_iter(), command)

    def build_use_flag_widget(self, use_flags, ebuild):
        """ Create a table layout and populate it with
            checkbox widgets representing the available
            use flags
        """
        debug.dprint("ADVEMERGE: build_use_flag_widget()")
        UseFlagFrame = self.wtree.get_object("frameUseFlags")
        #button_make_conf = self.wtree.get_object("button_make_conf")
        #button_package_use = self.wtree.get_object("button_package_use")
        # If frame has any children, remove them
        child = UseFlagFrame.get_child()
        if child != None:
            UseFlagFrame.remove(child)
        # If no use flags, hide the frame
        if not use_flags:
            UseFlagFrame.hide()
            self.btnMakeConf.hide()
            self.btnPkgUse.hide()
        else:
            UseFlagFrame.show()
            if self.is_root or utils.can_gksu():
                self.btnPkgUse.show()
                if config.Prefs.advemerge.show_make_conf_button:
                    self.btnMakeConf.show()
                else:
                    self.btnMakeConf.hide()
        # Build table to hold checkboxes
        uflag_widget = UseFlagWidget(use_flags, ebuild, self.window)
        uflag_widget.connect('grab-focus', self.on_toggled)
        UseFlagFrame.add(uflag_widget)
        uflag_widget.show()

    def build_keywords_widget(self, keywords):
        """ Create a table layout and populate it with
            checkbox widgets representing the available
            keywords
        """
        KeywordsFrame = self.wtree.get_object("frameKeywords")

        # If frame has any children, remove them
        child = KeywordsFrame.get_child()
        if child != None:
            KeywordsFrame.remove(child)

        # Build table to hold radiobuttons
        size = len(keywords) + 1  # Add one for None button
        maxcol = 5
        maxrow = size / maxcol - 1
        if maxrow < 1:
            maxrow = 1
        table = Gtk.Table(maxrow, maxcol-1, True)
        KeywordsFrame.add(table)
        self.kwList = []

        # Iterate through keywords, create
        # checkboxes and attach to table
        col = 0
        row = 0
        button = Gtk.RadioButton(label=_('None'))
        self.kwList.append([button, None])
        rbGroup = button
        table.attach(button, col, col+1, row, row+1)
        button.show()
        col += 1
        button_added = False
        clickable_button = False
        for keyword in keywords:
            if keyword[0] == '~' and (keyword[1:] == self.arch) or \
                        (config.Prefs.globals.enable_archlist and
                            ((keyword[1:] in config.Prefs.globals.archlist) or  (keyword in config.Prefs.globals.archlist))):
                button2 = Gtk.RadioButton.new_with_label_from_widget(rbGroup, label=keyword)
                self.kwList.append([button2, keyword])
                table.attach(button2, col, col+1, row, row+1)
                # connect to on_toggled so we can show changes
                button2.connect("toggled", self.on_toggled)
                button2.show()
                button_added = True
                clickable_button = True
                if keyword[1:] == self.arch and self.current_verInfo["stable"]:
                    # i.e. package has been keyword unmasked already
                    button2.set_active(True)
            else:
                #if (keyword == self.arch)
                label = Gtk.Label(label=keyword)
                label.set_alignment(.05, .5)
                label.set_use_underline(False)
                table.attach(label, col, col+1, row, row+1)
                label.show()
                button_added = True
            # Increment col & row counters
            if button_added:
                col += 1
                if col > maxcol:
                    col = 0
                    row += 1
        if clickable_button:
            # Display the entire table
            table.show()
            KeywordsFrame.show()
            if self.is_root or utils.can_gksu():
                self.btnPkgKeywords.show()
        else:
            KeywordsFrame.hide()
            self.btnPkgKeywords.hide()

