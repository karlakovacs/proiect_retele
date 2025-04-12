from enum import Enum


class RequestMessageType(Enum):
	LOGIN = 1
	LIST = 2
	CREATE = 3
	VIEW = 4
	EDIT = 5
	UPDATE = 6
	RELEASE = 7
	DELETE = 8
	LOGOUT = 9


class ResponseMessageType(Enum):
	OK = 1
	ERROR = 2
	FILES = 3
	CONTENT = 4
	INFO = 5


class RequestMessage:
	def __init__(self, message_type: RequestMessageType, payload=""):
		self.message_type = message_type
		self.payload = payload


class ResponseMessage:
	def __init__(self, message_type: ResponseMessageType, payload=""):
		self.message_type = message_type
		self.payload = payload

	def __str__(self):
		if self.message_type == ResponseMessageType.FILES or self.message_type == ResponseMessageType.CONTENT:
			return f"[{self.message_type.name}]\n{self.payload}"
		return f"[{self.message_type.name}] {self.payload}"
