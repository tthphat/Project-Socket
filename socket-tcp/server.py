import socket
import os
import threading


HOST = "172.172.26.165"
PORT = 65432
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


def perform_handshake_server(client_socket):
    """Thực hiện bắt tay ba bước từ phía server."""
    try:
        # Nhận SYN từ client
        syn_message = client_socket.recv(1024).decode(FORMAT)
        if syn_message != "SYN":
            raise Exception("Không nhận được SYN từ client.")


        # Gửi SYN-ACK đến client
        client_socket.sendall("SYN-ACK".encode(FORMAT))


        # Nhận ACK từ client
        ack_message = client_socket.recv(1024).decode(FORMAT)
        if ack_message != "ACK":
            raise Exception("Không nhận được ACK từ client.")


        print("Three-way handshake thành công với client.")
        return True
    except Exception as e:
        print(f"Lỗi trong bắt tay ba bước: {e}")
        return False


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


            if not perform_handshake_server(client_socket):
                print(f"Handshake thất bại với client {client_address}")
                return
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
        server.bind((HOST, PORT))
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











