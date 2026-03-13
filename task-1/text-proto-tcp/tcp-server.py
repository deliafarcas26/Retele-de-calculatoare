import socket
import threading

HOST = "127.0.0.1"
PORT = 3333
BUFFER_SIZE = 1024

class State:
    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()

    def add(self, key, value):
        with self.lock:
            self.data[key] = value

    def get(self, key):
        with self.lock:
            return self.data.get(key)

    def remove(self, key):
        with self.lock:
            return self.data.pop(key, None)

state = State()

def process_command(command):
    parts = command.split()
    if not parts:
        return "ERROR invalid command"

    cmd = parts[0].upper()
    args = parts[1:]

    if cmd == "ADD":
        if len(args) < 2:
            return "ERROR invalid command format"
        key = args[0]
        value = " ".join(args[1:])
        state.add(key, value)
        return "OK - record added"

    if cmd == "GET":
        if len(args) != 1:
            return "ERROR invalid command format"
        value = state.get(args[0])
        if value is None:
            return "ERROR invalid key"
        return f"DATA {value}"

    if cmd == "REMOVE":
        if len(args) != 1:
            return "ERROR invalid command format"
        value = state.remove(args[0])
        if value is None:
            return "ERROR invalid key"
        return f"OK {value} deleted"

    if cmd == "LIST":
        with state.lock:
            items = state.data.items()
        if not items:
            return "DATA|"
        pairs = ",".join(f"{k}={v}" for k, v in items)
        return f"DATA|{pairs}"

    if cmd == "COUNT":
        with state.lock:
            count = len(state.data)
        return f"DATA {count}"

    if cmd == "CLEAR":
        with state.lock:
            state.data.clear()
        return "all data deleted"

    if cmd == "UPDATE":
        if len(args) < 2:
            return "ERROR invalid command format"
        key = args[0]
        value = " ".join(args[1:])
        with state.lock:
            if key not in state.data:
                return "ERROR invalid key"
            state.data[key] = value
        return "Data updated"

    if cmd == "POP":
        if len(args) != 1:
            return "ERROR invalid command format"
        with state.lock:
            if args[0] not in state.data:
                return "ERROR invalid key"
            value = state.data.pop(args[0])
        return f"DATA {value}"

    if cmd == "QUIT":
        return None

    return "ERROR unknown command"

def handle_client(client_socket):
    with client_socket:
        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break

                command = data.decode('utf-8').strip()
                response = process_command(command)

                if response is None:
                    response = "OK"
                    response_data = f"{len(response)} {response}".encode('utf-8')
                    client_socket.sendall(response_data)
                    break

                response_data = f"{len(response)} {response}".encode('utf-8')
                client_socket.sendall(response_data)

            except Exception as e:
                client_socket.sendall(f"Error: {str(e)}".encode('utf-8'))
                break

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[SERVER] Listening on {HOST}:{PORT}")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"[SERVER] Connection from {addr}")
            threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_server()
