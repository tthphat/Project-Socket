import socket
import os
import threading

HOST = "127.0.0.1"
PORT = 55000
FORMAT = "utf8"
CHUNK_SIZE = 1024

def read_file(file_name):
    sending = ""
    try:
        with open(file_name, "r") as f:
            for line in f:
                if line.strip():
                    sending += line.strip() + '\n'
    except FileNotFoundError:
        print(f"File not found: {file_name}")
    return sending

# def send_chunk(conn, file_name, start_offset, chunk_size):
#     """Gửi một phần dữ liệu của file theo offset và kích thước chunk."""
#     try:
#         with open(file_name, "rb") as f:
#             f.seek(start_offset)  # Chuyển con trỏ tới offset
#             data = f.read(chunk_size)  # Đọc phần dữ liệu theo chunk_size

#             # Gửi dữ liệu cho client
#             conn.sendall(data)
#             print(f"Đã gửi chunk từ {start_offset} đến {start_offset + len(data)}")
#     except Exception as e:
#         print(f"Lỗi khi gửi chunk: {e}")


# def handle_download(conn, file_name):
#     file_size = os.path.getsize(file_name)
#     conn.sendall(str(file_size).encode(FORMAT))  # Gửi kích thước file

#     response = conn.recv(1024).decode(FORMAT)
#     print(response, "response1")  
#     if response == "CANCEL":
#         print(f"Client hủy tải file '{file_name}'.")
#         return

#     response = conn.recv(1024).decode(FORMAT)
#     print(response, "response2")
    # Nhận yêu cầu chunk và xử lý gửi chunk cho client
    # while True:
    #     chunk_request = conn.recv(1024).decode(FORMAT).strip()
    #     print(chunk_request)
    #     if chunk_request.startswith("CHUNK_REQUEST"):
    #         _, chunk_index, start, end = chunk_request.split(":")
    #         chunk_index = int(chunk_index)
    #         start = int(start)
    #         end = int(end)

    #         # Đọc chunk từ file và gửi nó đến client
    #         with open(file_name, "rb") as f:
    #             f.seek(start)
    #             data = f.read(end - start + 1)
    #             conn.sendall("DATA_START".encode(FORMAT))  # Gửi tín hiệu bắt đầu dữ liệu
    #             conn.sendall(data)  # Gửi dữ liệu chunk
    #             print(f"Đã gửi chunk {chunk_index} từ {start} đến {end}")

    #         conn.sendall("DATA_END".encode(FORMAT))  # Gửi tín hiệu kết thúc
    #     else:
    #         break  # Dừng nếu không nhận yêu cầu chunk


def send_chunk(client_socket, file_path, chunk_index, start, end):
    """Gửi một chunk dữ liệu từ start đến end."""
    try:
        # Đọc dữ liệu chunk từ file
        with open(file_path, "rb") as file:
            file.seek(start)
            remaining = end - start + 1

            # Gửi tín hiệu bắt đầu
            client_socket.sendall("DATA_START".encode(FORMAT))

            # Gửi dữ liệu theo từng gói nhỏ
            while remaining > 0:
                data = file.read(min(CHUNK_SIZE, remaining))
                if not data:
                    break
                client_socket.sendall(data)
                remaining -= len(data)

            # Gửi tín hiệu kết thúc
            client_socket.sendall("DATA_END".encode(FORMAT))
        print(f"Đã gửi chunk {chunk_index}: {start}-{end}.")
    except Exception as e:
        print(f"Lỗi khi gửi chunk {chunk_index}: {e}")


def handle_chunk_connection(client_socket):
    """Xử lý yêu cầu tải chunk từ client."""
    try:
        # Gửi tín hiệu sẵn sàng
        client_socket.sendall("READY".encode(FORMAT))

        # Nhận yêu cầu chunk
        chunk_request = client_socket.recv(1024).decode(FORMAT)

        print(chunk_request, "skubudu")
        if not chunk_request.startswith("CHUNK_REQUEST"):
            raise Exception("Yêu cầu không hợp lệ.")
        
        # Tách thông tin yêu cầu
        _, file_name, chunk_index, start, end = chunk_request.split(":")
        chunk_index, start, end = int(chunk_index), int(start), int(end)

        # Gửi chunk dữ liệu
        send_chunk(client_socket, file_name, chunk_index, start, end)
    except Exception as e:
        print(f"Lỗi khi xử lý chunk: {e}")
    finally:
        client_socket.close()


def handle_client(client_socket, client_address):
    """Xử lý kết nối từ client."""
    try:
    
        client_type = client_socket.recv(1024).decode(FORMAT)

        if client_type == "CLIENT":
            print(f"Client {client_address} đã kết nối.")
            # Gửi danh sách file
            client_socket.sendall(read_file("files.txt").encode(FORMAT))

            while True:
                # Nhận yêu cầu tải file từ client
                file_request = client_socket.recv(1024).decode(FORMAT)
                if not file_request:
                    break
               
                print(f"Client {client_address} yêu cầu tải file: {file_request}")

                if os.path.exists(file_request):
                    client_socket.sendall("OK".encode(FORMAT))

                    # Gửi kích thước file
                    file_size = os.path.getsize(file_request)
                    client_socket.sendall(str(file_size).encode(FORMAT))

                else:
                    client_socket.sendall("NOT_FOUND".encode(FORMAT))
        elif client_type == "CHUNK":
            handle_chunk_connection(client_socket)
        else:
            print(f"Loại client không hợp lệ: {client_type}")
    except Exception as e:
        print(f"Lỗi khi xử lý client {client_address}: {e}")
    finally:
        client_socket.close()
        print(f"Client {client_address} đã ngắt kết nối.")




def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))  # Bind the socket to the host and port
        server.listen()
        print(f"Server started on {HOST}:{PORT}")
       
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

def main():
    try:
        run_server()
    except KeyboardInterrupt:
        print(f"Server ngừng hoạt động!")
    except Exception as E:
        print(f"Error: {E}")

if __name__ == "__main__":
    main()