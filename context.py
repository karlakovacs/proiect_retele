class Context:
	def __init__(self, socket):
		self.logged_in = False
		self.viewing_file = None
		self.view_active = False
		self.socket = socket
