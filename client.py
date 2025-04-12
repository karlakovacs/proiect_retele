import socket
import threading

from connection import BUFFER_SIZE, HOST_CLIENT, PORT
from context import Context
from printing import Color, print_color
from serialization import deserialize, serialize
from transfer_units import RequestMessage, RequestMessageType, ResponseMessage, ResponseMessageType


def prompt_multiline(end_marker: str = "EOF"):
	print_color(f"Enter content (end with `{end_marker}`):", Color.BLUE)
	lines = []
	while True:
		line = input()
		if line.strip() == end_marker:
			break
		lines.append(line)
	return "\n".join(lines)


def wait_for_exit_view(context: Context):
	while context.view_active:
		user_input = input().strip().upper()
		if user_input == "X":
			context.viewing_file = None
			context.view_active = False
			print_color("Exited VIEW mode", Color.BLUE)


def receiver_loop(context: Context):
	sock: socket.socket = context.socket
	while True:
		try:
			data: bytes = sock.recv(BUFFER_SIZE)
			if not data:
				break

			response: ResponseMessage = deserialize(data)

			if response.message_type == ResponseMessageType.OK:
				print_color(response, Color.GREEN)
				if response.payload.startswith("Logged in"):
					context.logged_in = True

			elif response.message_type == ResponseMessageType.CONTENT:
				filename, _ = response.payload.split("\n", 1)
				if context.viewing_file and filename.startswith(context.viewing_file):
					print_color(response, Color.PURPLE)
					print_color("(Press X and Enter to exit VIEW mode)", Color.BLUE)

			elif response.message_type == ResponseMessageType.FILES:
				print_color(response, Color.PURPLE)

			elif response.message_type == ResponseMessageType.ERROR:
				print_color(response, Color.RED)

			elif response.message_type == ResponseMessageType.INFO:
				print_color(response, Color.CYAN)
		except Exception as e:
			print_color(f"[ERROR] {e}", Color.RED)
			break


def main():
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.connect((HOST_CLIENT, PORT))
	context = Context(client_socket)
	threading.Thread(target=receiver_loop, args=(context,), daemon=True).start()

	while True:
		if context.viewing_file:
			continue

		cmd = input("").strip()
		if not cmd:
			continue

		parts = cmd.split(" ", 1)
		command = parts[0].upper()
		payload = parts[1] if len(parts) > 1 else ""

		if command == RequestMessageType.LOGIN.name and not context.logged_in:
			if not payload:
				print_color("[USAGE] LOGIN <username>", Color.YELLOW)
				continue
			msg = RequestMessage(RequestMessageType.LOGIN, payload)
			client_socket.sendall(serialize(msg))
			continue

		if not context.logged_in:
			print_color("[ERROR] You must LOGIN first", Color.RED)
			continue

		if command == RequestMessageType.EDIT.name:
			if not payload:
				print_color("[USAGE] EDIT <username>", Color.YELLOW)
				continue
			msg = RequestMessage(RequestMessageType.EDIT, payload)

		elif command == RequestMessageType.UPDATE.name:
			if not payload:
				print_color("[USAGE] UPDATE <filename>", Color.YELLOW)
				continue
			content = prompt_multiline()
			msg = RequestMessage(RequestMessageType.UPDATE, f"{payload}\n{content}")

		elif command == RequestMessageType.RELEASE.name:
			if not payload:
				print_color("[USAGE] RELEASE <filename>", Color.YELLOW)
				continue
			msg = RequestMessage(RequestMessageType.RELEASE, payload)

		elif command == RequestMessageType.LIST.name:
			msg = RequestMessage(RequestMessageType.LIST)

		elif command == RequestMessageType.CREATE.name:
			if not payload:
				print_color("[USAGE] CREATE <filename>", Color.YELLOW)
				continue
			content = prompt_multiline()
			msg = RequestMessage(RequestMessageType.CREATE, f"{payload}\n{content}")

		elif command == RequestMessageType.VIEW.name:
			if not payload:
				print_color("[USAGE] VIEW <filename>", Color.YELLOW)
				continue
			msg = RequestMessage(RequestMessageType.VIEW, payload)
			client_socket.sendall(serialize(msg))
			context.viewing_file = payload.strip()
			context.view_active = True
			threading.Thread(target=wait_for_exit_view, args=(context,), daemon=True).start()
			continue

		elif command == RequestMessageType.DELETE.name:
			if not payload:
				print_color("[USAGE] DELETE <filename>", Color.YELLOW)
				continue
			msg = RequestMessage(RequestMessageType.DELETE, payload)

		elif command == RequestMessageType.LOGOUT.name:
			msg = RequestMessage(RequestMessageType.LOGOUT)
			client_socket.sendall(serialize(msg))
			break

		else:
			print_color("[ERROR] Unknown command", Color.RED)
			continue

		client_socket.sendall(serialize(msg))


if __name__ == "__main__":
	main()
