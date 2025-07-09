#! /usr/bin/env python
"""
    Porthole dispatcher module
    Holds common debug functions for Porthole

    Copyright (C) 2003 - 2008 Fredrik Arnerup, Brian Dolbec

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

# Fredrik Arnerup <foo@stacken.kth.se>, 2004-12-19
# Brian Dolbec<dol-sen@telus.net>,2005-3-30

from gi.repository import GObject
import os
import queue
from select import select
from sys import stderr
import _thread
import time
import threading


class Dispatcher:
    """Send signals from a thread to another thread through a pipe
    in a thread-safe manner"""
    def __init__(self, callback_func, *args, **kwargs):
        self.callback = callback_func
        self.callback_args = args
        self.callback_kwargs = kwargs
        self.continue_io_watch = True
        self.queue = queue.Queue(0) # thread safe queue
        self.pipe_r, self.pipe_w = os.pipe()
        GObject.io_add_watch(self.pipe_r, GObject.IO_IN, self.on_data)

    def __call__(self, *args):
        """Emit signal from thread"""
        self.queue.put(args)
        # write to pipe afterwards
        os.write(self.pipe_w, b"X")

    def on_data(self, source, cb_condition):
        if select([self.pipe_r],[],[], 0)[0] and os.read(self.pipe_r,1):
            if self.callback_args:
                args = self.callback_args + self.queue.get()
                self.callback(*args, **self.callback_kwargs)
            else:
                self.callback(*self.queue.get(), **self.callback_kwargs)
        return self.continue_io_watch


class Dispatch_wait:
    """Send signals from a thread to another thread through a pipe
    in a thread-safe manner. wait for data to return"""
    def __init__(self, callback_func, *args, **kwargs):
        self.callback = callback_func
        self.callback_args = args
        self.callback_kwargs = kwargs
        self.continue_io_watch = True
        self.queue = queue.Queue(0) # thread safe queue
        self.reply = queue.Queue(0)
        self.callpipe_r, self.callpipe_w = os.pipe()
        self.wait = {}  # dict of boolleans for incoming thread id's waiting for replies
        self.semaphore = threading.Semaphore()
        GObject.io_add_watch(self.callpipe_r, GObject.IO_IN, self.on_calldata)

    def __call__(self, *args):  # this function is running in the calling thread
        """Emit signal from thread"""
        _id = _thread.get_ident()
        self.queue.put([args, _id])
        # write to pipe afterwards
        os.write(self.callpipe_w, b"X")
        # now wait for the reply
        self.semaphore.acquire()
        self.wait[_id] = True
        self.semaphore.release()
        # fixme hidden *args
        while self.wait[_id]:
            #pass the time waiting for a reply by having a snooze
            time.sleep(0.01)
        myreply, reply_id = self.reply.get()
        if reply_id != _id:
            print("DISPATCH_WAIT:  Uh-Oh! id's do not match!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", file=stderr)
        return myreply


    def on_calldata(self, source, cb_condition):
        if select([self.callpipe_r],[],[], 0)[0] and os.read(self.callpipe_r,1):
            args, _id =self.queue.get()
            if self.callback_args:
                reply = self.callback(*( self.callback_args + args), **self.callback_kwargs)
            else:
                reply = self.callback(*args, **self.callback_kwargs)
            self.semaphore.acquire()
            self.reply.put([reply, _id])
            self.wait[_id] = False
            self.semaphore.release()
        return self.continue_io_watch
