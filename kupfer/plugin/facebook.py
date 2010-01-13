from __future__ import absolute_import

from kupfer.objects import Leaf, Action, Source
from kupfer.objects import (TextLeaf, UrlLeaf, RunnableLeaf, FileLeaf,
		AppLeafContentMixin )
from kupfer import utils
from kupfer.helplib import FilesystemWatchMixin
from kupfer.obj.contacts import EMAIL_KEY, ContactLeaf
from kupfer.obj.grouping import ToplevelGroupingSource

__kupfer_name__ = _("Facebook")
__kupfer_sources__ = ("ContactsSource", )
#__kupfer_actions__ = ("NewMailAction", "SendFileByMail")
#__description__ = _("Claws Mail Contacts and Actions")
__version__ = "2010-01-06"
__author__ = "Ulrik Sverdrup <ulrik.sverdrup@gmail.com>"

import facebook

API_KEY = "832b734b048412cd714707e9f25c7029"
S_KEY = ""


class AuthorizeInFacebook (RunnableLeaf):
	def __init__(self):
		RunnableLeaf.__init__(self, name=_("Authorize in Facebook"))
	def run(self):
		ContactsSource.authorize()

class AuthorizationOK (RunnableLeaf):
	def __init__(self):
		RunnableLeaf.__init__(self, name=_("Authorization Finished"))
	def run(self):
		ContactsSource.authorize_finish()

class OpenProfileURL (Action):
	def __init__(self):
		Action.__init__(self, _("Open"))
	def activate(self, leaf):
		utils.show_url(leaf.object["profile_url"])
	def get_icon_name(self):
		return "forward"

class Contact (ContactLeaf):
	def get_actions(self):
		yield OpenProfileURL()


ToplevelGroupingSource = Source
class ContactsSource (ToplevelGroupingSource):
	shared_instance = None
	def __init__(self, name=_("Facebook")):
		ToplevelGroupingSource.__init__(self, _("Facebook")) #, "Contacts")
		self._version = 2
		self._session_data = {}

	def initialize(self):
		ToplevelGroupingSource.initialize(self)
		ContactsSource.shared_instance = self
		self.connection = facebook.Facebook(API_KEY, S_KEY)
		if self._session_data:
			self.connection.session_key = self._session_data["session_key"]
			self.connection.secret = self._session_data["secret"]
	
	@classmethod
	def authorize(cls):
		cls.shared_instance._authorize()
	def _authorize(self):
		self.connection = facebook.Facebook(API_KEY, S_KEY)
		self.connection.auth.createToken()
		self.connection.login()

	@classmethod
	def authorize_finish(cls):
		cls.shared_instance._authorize_finish()
	def _authorize_finish(self):
		self._session_data = self.connection.auth.getSession()
		self.mark_for_update()

	def _new_connection(self):
		connection = facebook.Facebook(API_KEY, S_KEY)
		print "create token"
		connection.auth.createToken()
		connection.login()
		return connection

	def get_items(self):
		print "GET ITEMS"
		#connection = facebook.Facebook(API_KEY, S_KEY)
		#self.connection.session_key = self._session_data["session_key"]
		#self.connection.auth.createToken()
		if not self._session_data:
			yield AuthorizeInFacebook()
			yield AuthorizationOK()
			return
		try:
			self.connection.users.getLoggedInUser()
		except facebook.FacebookError, exc:
			self.output_error(type(exc).__name__, exc)
			self._session_data = None
			self.mark_for_update()
			return
		friend_ids = self.connection.friends.get()
		print friend_ids
		friends = self.connection.users.getInfo(friend_ids, fields=["pic_square", "profile_url", "name", "uid"])
		print friends
		for friend in friends:
			yield Contact(friend, friend["name"])
		

	def get_description(self):
		return None

	def provides(self):
		yield ContactLeaf


