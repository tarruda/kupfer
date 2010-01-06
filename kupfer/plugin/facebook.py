from __future__ import absolute_import

from kupfer.objects import Leaf, Action, Source
from kupfer.objects import (TextLeaf, UrlLeaf, RunnableLeaf, FileLeaf,
		AppLeafContentMixin )
from kupfer import utils
from kupfer.helplib import FilesystemWatchMixin
from kupfer.obj.grouping import EMAIL_KEY, ContactLeaf, ToplevelGroupingSource

__kupfer_name__ = _("Facebook")
__kupfer_sources__ = ("ContactsSource", )
#__kupfer_actions__ = ("NewMailAction", "SendFileByMail")
#__description__ = _("Claws Mail Contacts and Actions")
__version__ = "2010-01-06"
__author__ = "Ulrik Sverdrup <ulrik.sverdrup@gmail.com>"

import facebook



class Contact (ContactLeaf):
	pass
	

class SendFileByMail(Action):
	''' Createn new mail and attach selected file'''
	def __init__(self):
		Action.__init__(self, _('Send by Email'))

	def activate(self, leaf):
		filepath = leaf.object
		utils.launch_commandline("claws-mail --attach '%s'" % filepath)

	def get_icon_name(self):
		return "mail-message-new"

	def item_types(self):
		yield FileLeaf

	def get_description(self):
		return _("Compose new email in ClawsMail and attach file")

	def valid_for_item(self, item):
		return os.path.isfile(item.object)


API_KEY = "832b734b048412cd714707e9f25c7029"
S_KEY = ""

ToplevelGroupingSource = Source
class ContactsSource (ToplevelGroupingSource):
	def __init__(self, name=_("Claws Mail Address Book")):
		ToplevelGroupingSource.__init__(self, _("Facebook")) #, "Contacts")
		self._version = 1
		self._session_data = {}

	def initialize(self):
		ToplevelGroupingSource.initialize(self)
		if self._session_data:
			self.connection = facebook.Facebook(API_KEY, S_KEY)
			self.connection.session_key = self._session_data["session_key"]
		else:
			self.connection = self._new_connection()
			print "create token"
			self.connection.auth.createToken()
			self.connection.login()
	
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
		try:
			self._session_data = self.connection.auth.getSession()
		finally:
			self.connection = self._new_connection()
			self._session_data = self.connection.auth.getSession()
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


