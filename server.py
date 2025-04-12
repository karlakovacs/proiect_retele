import os
import socket
import threading

from connection import BUFFER_SIZE, HOST, PORT, SHARED_DIR
from printing import Color, print_color
from serialization import deserialize, serialize
from state import State
from transfer_units import RequestMessage, RequestMessageType, ResponseMessage, ResponseMessageType


state = State()


def broadcast(response: str, exclude_username: str = None):
	for user, conn in state.connections.items():
		if user != exclude_username:
			try:
				conn.sendall(serialize(response))
			except:
				pass


def handle_client(conn: socket.socket):
	username = None
	try:
		while True:
			data = conn.recv(BUFFER_SIZE)
			if not data:
				break

			request: RequestMessage = deserialize(data)

			if request.message_type == RequestMessageType.LOGIN:
				username = request.payload.strip()
				success = state.add_connection(username, conn)
				if not success:
					response = ResponseMessage(ResponseMessageType.ERROR, f"Username '{username}' already in use")
				else:
					response = ResponseMessage(ResponseMessageType.OK, f"Logged in as {username}")

			elif request.message_type == RequestMessageType.LIST:
				files = state.get_file_list()
				response = ResponseMessage(ResponseMessageType.FILES, "\n".join(files))

			elif request.message_type == RequestMessageType.CREATE:
				try:
					filename, content = request.payload.split("\n", 1)
					result = state.create_file(filename.strip(), content)
					if result is True:
						response = ResponseMessage(ResponseMessageType.OK, f"File '{filename}' created")
						broadcast(
							ResponseMessage(ResponseMessageType.INFO, f"{username} created file '{filename}'"),
							exclude_username=username,
						)
					else:
						response = ResponseMessage(ResponseMessageType.ERROR, result)
				except ValueError:
					response = ResponseMessage(ResponseMessageType.ERROR, "Invalid payload format")

			elif request.message_type == RequestMessageType.VIEW:
				filename = request.payload.strip()
				content = state.view_file(filename, username)
				if content is not None:
					response = ResponseMessage(ResponseMessageType.CONTENT, f"{filename}\n{content}")
				else:
					response = ResponseMessage(ResponseMessageType.ERROR, "File not found")

			elif request.message_type == RequestMessageType.EDIT:
				filename = request.payload.strip()
				success, message = state.edit_file(filename, username)
				if success:
					response = ResponseMessage(ResponseMessageType.OK, message)
					broadcast(
						ResponseMessage(ResponseMessageType.INFO, f"{username} started editing '{filename}'"),
						exclude_username=username,
					)
				else:
					response = ResponseMessage(ResponseMessageType.ERROR, message)

			elif request.message_type == RequestMessageType.UPDATE:
				try:
					filename, content = request.payload.split("\n", 1)
					updated = state.update_file(filename.strip(), content, username)
					if updated is True:
						response = ResponseMessage(ResponseMessageType.OK, f"File '{filename}' updated")
						viewers = state.get_viewers(filename)
						update_msg = ResponseMessage(
							ResponseMessageType.CONTENT, f"{filename} (updated by {username})\n{content}"
						)
						for viewer in viewers:
							if viewer != username and viewer in state.connections:
								try:
									state.connections[viewer].sendall(serialize(update_msg))
								except:
									pass
					else:
						response = ResponseMessage(ResponseMessageType.ERROR, updated)
				except ValueError:
					response = ResponseMessage(ResponseMessageType.ERROR, "Invalid payload format")

			elif request.message_type == RequestMessageType.RELEASE:
				filename = request.payload.strip()
				result = state.release_file(filename, username)
				if result is True:
					response = ResponseMessage(ResponseMessageType.OK, f"Released file '{filename}'")
					broadcast(
						ResponseMessage(ResponseMessageType.INFO, f"{username} released '{filename}'"),
						exclude_username=username,
					)
				else:
					response = ResponseMessage(ResponseMessageType.ERROR, result)

			elif request.message_type == RequestMessageType.DELETE:
				filename = request.payload.strip()
				result = state.delete_file(filename)
				if result is True:
					response = ResponseMessage(ResponseMessageType.OK, f"File '{filename}' deleted")
					broadcast(
						ResponseMessage(ResponseMessageType.INFO, f"{username} deleted '{filename}'"),
						exclude_username=username,
					)
				else:
					response = ResponseMessage(ResponseMessageType.ERROR, result)

			elif request.message_type == RequestMessageType.LOGOUT:
				state.remove_connection(username)
				response = ResponseMessage(ResponseMessageType.OK, "Disconnected")
				conn.sendall(serialize(response))
				break

			else:
				response = ResponseMessage(ResponseMessageType.ERROR, "Unknown command")

			conn.sendall(serialize(response))

	except Exception as e:
		print_color(f"[ERROR] {e}", Color.RED)
	finally:
		conn.close()
		if username:
			state.remove_connection(username)
			print_color(f"[INFO] Client {username} disconnected", Color.PURPLE)


def main():
	if not os.path.exists(SHARED_DIR):
		os.makedirs(SHARED_DIR)

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
		server_socket.bind((HOST, PORT))
		server_socket.listen()
		print_color(f"[INFO] Server running on {HOST}:{PORT}", Color.GREEN)

		while True:
			try:
				conn, address = server_socket.accept()
				print_color(f"[INFO] Connection from {address}", Color.CYAN)
				threading.Thread(target=handle_client, args=(conn,), daemon=True).start()
			except Exception as e:
				print_color(f"[ERROR] {e}", Color.RED)


if __name__ == "__main__":
	main()
