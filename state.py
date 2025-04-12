import os

from connection import SHARED_DIR


class State:
	def __init__(self):
		self.connections: dict = {}  # username -> conn
		self.file_status: dict = {}  # filename -> {'editor': username, 'viewers': set()}

	def _ensure_file_entry(self, filename):
		if filename not in self.file_status:
			self.file_status[filename] = {"editor": None, "viewers": set()}

	def add_connection(self, username, conn):
		if username in self.connections:
			return False
		self.connections[username] = conn
		return True

	def remove_connection(self, username):
		self.connections.pop(username, None)
		for status in self.file_status.values():
			if status["editor"] == username:
				status["editor"] = None
			status["viewers"].discard(username)

	def get_file_list(self):
		files = [f for f in os.listdir(SHARED_DIR) if f.endswith(".txt")]
		for f in files:
			self._ensure_file_entry(f)
		return [
			f"{f}: editing by {self.file_status[f]['editor']}" if self.file_status[f]["editor"] else f"{f}: available"
			for f in files
		]

	def create_file(self, filename, content):
		path = os.path.join(SHARED_DIR, filename)
		if os.path.exists(path):
			return "File already exists"
		with open(path, "w") as f:
			f.write(content)
		self._ensure_file_entry(filename)
		return True

	def delete_file(self, filename):
		path = os.path.join(SHARED_DIR, filename)
		if not os.path.exists(path):
			return "File does not exist"
		if self.file_status.get(filename, {}).get("editor"):
			return "File is currently being edited"
		os.remove(path)
		self.file_status.pop(filename, None)
		return True

	def view_file(self, filename, username):
		path = os.path.join(SHARED_DIR, filename)
		if not os.path.exists(path):
			return None
		self._ensure_file_entry(filename)
		self.file_status[filename]["viewers"].add(username)
		with open(path, "r") as f:
			return f.read()

	def add_viewer(self, filename, username):
		self._ensure_file_entry(filename)
		self.file_status[filename]["viewers"].add(username)

	def remove_viewer(self, filename, username):
		if filename in self.file_status:
			self.file_status[filename]["viewers"].discard(username)

	def edit_file(self, filename, username):
		path = os.path.join(SHARED_DIR, filename)
		if not os.path.exists(path):
			return False, "File does not exist"
		self._ensure_file_entry(filename)
		if self.file_status[filename]["editor"]:
			return False, "File is already being edited"
		self.file_status[filename]["editor"] = username
		self.file_status[filename]["viewers"].add(username)
		return True, f"You are now the editor of {filename}"

	def update_file(self, filename, content, username):
		if self.file_status.get(filename, {}).get("editor") != username:
			return "You are not the editor of this file"
		path = os.path.join(SHARED_DIR, filename)
		with open(path, "w") as f:
			f.write(content)
		return True

	def release_file(self, filename, username):
		if self.file_status.get(filename, {}).get("editor") != username:
			return "You are not the editor"
		self.file_status[filename]["editor"] = None
		self.file_status[filename]["viewers"].discard(username)
		return True

	def get_viewers(self, filename):
		return self.file_status.get(filename, {}).get("viewers", set())
