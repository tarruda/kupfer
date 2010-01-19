from __future__ import absolute_import

from kupfer.objects import Leaf, Action, Source
from kupfer.objects import (TextLeaf, UrlLeaf, RunnableLeaf, FileLeaf,
		AppLeafContentMixin )
from kupfer import utils
from kupfer.helplib import FilesystemWatchMixin, PicklingHelperMixin
from kupfer.obj.contacts import EMAIL_KEY, ContactLeaf
from kupfer.obj.grouping import ToplevelGroupingSource
from kupfer import task

__kupfer_name__ = _("Facebook")
__kupfer_sources__ = ("ContactsSource", )
__kupfer_actions__ = (
	"UpdateStatus",
)
__description__ = ""
__version__ = "2010-01-06"
__author__ = "Ulrik Sverdrup <ulrik.sverdrup@gmail.com>"

import facebook

API_KEY = ("832b734b048412cd714707e9f25c7029",
           "dda4672a05eb3003fb5eab8a7b34cb42")


class DoNothingLeaf (Leaf):
	def __init__(self, name):
		Leaf.__init__(self, name, name)

class AuthorizeInFacebook (RunnableLeaf):
	def __init__(self):
		RunnableLeaf.__init__(self, name=_("1. Authorize in Facebook"))
	def run(self):
		ContactsSource.authorize()

class AuthorizationOK (RunnableLeaf):
	def __init__(self):
		RunnableLeaf.__init__(self, name=_("2. Authorization Finished"))
	def run(self):
		ContactsSource.authorize_finish()

class LogOut (RunnableLeaf):
	def __init__(self):
		RunnableLeaf.__init__(self, name=_("Log Out From Facebook"))
	def run(self):
		ContactsSource.logout()

class OpenProfileURL (Action):
	def __init__(self):
		Action.__init__(self, _("Open"))
	def activate(self, leaf):
		utils.show_url(leaf.object["profile_url"])
	def get_icon_name(self):
		return "forward"

class UpdateStatus (Action):
	def __init__(self):
		Action.__init__(self, _("Update Status"))

	def item_types(self):
		yield TextLeaf

	def activate(self, leaf):
		text = leaf.object
		ContactsSource.update_status(text)

	def get_description(self):
		return _("Update your facebook status")

class Contact (ContactLeaf):
	def get_actions(self):
		yield OpenProfileURL()


class DownloadTask (task.ThreadTask):
	def __init__(self, connection, owner):
		task.ThreadTask.__init__(self)
		self.connection = connection
		self.owner = owner
		self.fail = False
		self.contacts = []

	def thread_do(self):
		try:
			self.connection.users.getLoggedInUser()
		except facebook.FacebookError, exc:
			self.fail = exc
			return
		friend_ids = self.connection.friends.get()
		print friend_ids
		friends = self.connection.users.getInfo(friend_ids, fields=["pic_square", "profile_url", "name", "uid"])
		print friends
		self.contacts = [Contact(friend, friend["name"]) for friend in friends]

	def thread_finish(self):
		if self.fail:
			self.owner.output_error("Error when downloading", self.fail)
			self.owner._session_data = None
			self.owner.mark_for_update()
		else:
			self.owner.contacts = self.contacts
			self.owner.mark_for_update()

class ContactsSource (Source, PicklingHelperMixin):
	shared_instance = None
	def __init__(self, name=_("Facebook")):
		Source.__init__(self, _("Facebook"))
		self._version = 2
		self._session_data = {}

	def pickle_prepare(self):
		self.task_runner = None

	def initialize(self):
		self.task_runner = task.TaskRunner(True)
		self.contacts = []
		ContactsSource.shared_instance = self
		self.connection = facebook.Facebook(*API_KEY)
		if self._session_data:
			self.connection.session_key = self._session_data["session_key"]
			self.connection.secret = self._session_data["secret"]
	
	@classmethod
	def authorize(cls):
		cls.shared_instance._authorize()

	def _authorize(self):
		self.connection = facebook.Facebook(*API_KEY)
		self.connection.auth.createToken()
		self.connection.login()

	@classmethod
	def authorize_finish(cls):
		cls.shared_instance._authorize_finish()

	def _authorize_finish(self):
		self._session_data = self.connection.auth.getSession()
		self.mark_for_update()

	@classmethod
	def update_status(cls, text):
		cls.shared_instance._update_status(text)

	def _update_status(self, text):
		try:
			self.connection.users.setStatus(text, False)
		except facebook.FacebookError, exc:
			print exc, dir(exc)
			print exc.code
			# extended permission needed
			if exc.code == 250:
				self.connection.request_extended_permission("publish_stream")

	def get_items(self):
		print "GET ITEMS"
		if not self._session_data:
			yield AuthorizeInFacebook()
			yield AuthorizationOK()
			self.contacts = []
			return
		if self.contacts:
			for C in self.contacts:
				yield C
		else:
			self.task_runner.add_task(DownloadTask(self.connection, self))
			yield DoNothingLeaf(_("Downloading Friend List"))
		
	def should_sort_lexically(self):
		return True

	def get_description(self):
		return None

	def provides(self):
		yield ContactLeaf


