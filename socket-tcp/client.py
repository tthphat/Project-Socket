import socket
import time
import threading
import os
from tkinter import filedialog
from tqdm import tqdm


host = "172.172.26.163"
port = 65432 
FORMAT = "utf8"
progress = [0] * 4


def perform_handshake_client(client_socket):
    """Thực hiện bắt tay ba bước từ phía client."""
    try:
        # Gửi SYN đến server
        client_socket.sendall("SYN".encode(FORMAT))
        time.sleep(0.5)
        
        


        # Nhận SYN-ACK từ server
        syn_ack_message = client_socket.recv(1024).decode(FORMAT)
        if syn_ack_message != "SYN-ACK":
            raise Exception("Không nhận được SYN-ACK từ server.")


        # Gửi ACK đến server
        client_socket.sendall("ACK".encode(FORMAT))
        time.sleep(0.5)
        
        print("Three-way handshake thành công với server.")
        return True
    except Exception as e:
        print(f"Lỗi trong bắt tay ba bước: {e}")
        return False


def read_new_files(file_name, already_downloaded):
    try:
        with open(file_name, "r") as f:
            lines = f.readlines()
            new_files = [line.strip() for line in lines if line.strip() not in already_downloaded]
            return new_files
    except FileNotFoundError:
        print(f"File '{file_name}' không tồn tại.")
        return []
    except Exception as e:
        print(f"Có lỗi khi đọc file '{file_name}': {e}")
        return []




def merge_chunks(chunks, output_file):
    """Gộp các chunk thành file hoàn chỉnh."""
    try:
        # Đảm bảo chunk được gộp theo thứ tự
        chunks.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
       
        with open(output_file, 'wb') as out_file:
            for chunk_file in chunks:
                with open(chunk_file, 'rb') as chunk:
                    data = chunk.read()
                    out_file.write(data)
                    print(f"Đã gộp {chunk_file} ({len(data)} bytes) vào {output_file}")


        print(f"File hợp nhất: {output_file}")
    except Exception as e:
        print(f"Lỗi khi tạo file {output_file}: {e}")




def download_chunk(host, port, file_name, chunk_paths, chunk_index, start, end, download_folder_path, total_progress):
    """Tải xuống một chunk từ server."""
    try:
        # Tạo socket riêng cho mỗi thread
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        client_socket.sendall("CHUNK".encode(FORMAT))  # Gửi tín hiệu là chunk
        time.sleep(0.5)


        response = client_socket.recv(1024).decode(FORMAT)
        if response != "READY":
            raise Exception("Server không sẵn sàng để nhận chunk.")


        # Gửi yêu cầu tải chunk với start và end
        request = f"CHUNK_REQUEST:{file_name}:{chunk_index}:{start}:{end}"
        client_socket.sendall(request.encode(FORMAT))
        time.sleep(0.5)


        # Nhận phản hồi bắt đầu
        response = client_socket.recv(1024).decode(FORMAT).strip()
        if response != "DATA_START":
            raise Exception("Không nhận được tín hiệu bắt đầu dữ liệu.")


        # Nhận dữ liệu chunk
        chunk_data = bytearray()
        total_received = 0
        chunk_size = end - start + 1


        # Tạo thanh tiến trình cho chunk
        chunk_progress = tqdm(
            total=chunk_size,
            desc=f"Chunk {chunk_index}",
            unit="B",
            unit_scale=True,
            position=chunk_index
        )


        while total_received < chunk_size:
            packet = client_socket.recv(min(1024, chunk_size - total_received))
            if not packet:
                break
            chunk_data += packet
            total_received += len(packet)


            # Cập nhật thanh tiến trình của chunk
            chunk_progress.update(len(packet))
            # Cập nhật tiến trình tổng
            total_progress[0] += len(packet)
            time.sleep(0.05)


        chunk_progress.close()


        # Nhận tín hiệu kết thúc
        response = client_socket.recv(1024).decode(FORMAT).strip()
        if response != "DATA_END":
            raise Exception("Không nhận được tín hiệu kết thúc dữ liệu.")


        # Lưu dữ liệu chunk
        chunk_paths[chunk_index] = chunk_data


    except Exception as e:
        print(f"Lỗi khi tải chunk {chunk_index}: {e}")
    finally:
        client_socket.close()
        chunk_progress.close()




def download_file(client, file_name):
    """Tải xuống file từ server theo từng chunk."""
    try:
        # Nhận kích thước file từ server
        file_size = int(client.recv(1024).decode(FORMAT).strip())


        # Chọn thư mục để lưu file
        download_folder_path = filedialog.askdirectory(title=f"Chọn thư mục lưu file {file_name}")
        if not download_folder_path:
            print("Chưa chọn thư mục tải về. Hủy quá trình tải.")
            client.sendall("CANCEL".encode(FORMAT))
            time.sleep(1)
            return


        # Chia kích thước file thành các chunk
        num_chunks = 4  # Số chunk = 4
        chunk_size = file_size // num_chunks
        threads = []
        chunk_paths = [None] * num_chunks  # Khởi tạo danh sách với số phần tử bằng số chunk
        total_progress = [0]  # Tổng số bytes đã tải


        # Tạo thanh tiến trình tổng
        # total_bar = tqdm(
        #     total=file_size,
        #     desc="Tổng tiến trình",
        #     unit="B",
        #     unit_scale=True,
        #     position=num_chunks
        # )


        for i in range(num_chunks):
            start = i * chunk_size
            end = file_size - 1 if i == num_chunks - 1 else (start + chunk_size - 1)
            thread = threading.Thread(
                target=download_chunk,
                args=(host, port, file_name, chunk_paths, i, start, end, download_folder_path, total_progress)
            )
            threads.append(thread)
            thread.start()


        # Cập nhật thanh tiến trình tổng trong khi tải
        # while any(thread.is_alive() for thread in threads):
        #     total_bar.n = total_progress[0]
        #     total_bar.refresh()
        #     time.sleep(0.1)

        # Chờ tất cả các thread hoàn thành
        for thread in threads:
            thread.join()


        total_bar.close()


        # Gộp các chunk lại thành file hoàn chỉnh
        output_file_path = os.path.join(download_folder_path, file_name)
        with open(output_file_path, 'wb') as f:
            for chunk_data in chunk_paths:
                if chunk_data is not None:
                    f.write(chunk_data)


        time.sleep(2)
        print(f"File '{file_name}' đã được tải xuống thành công tại {output_file_path}.")


    except Exception as e:
        print(f"Lỗi khi tải file: {e}")


def monitor(client, file_name):
    already_downloaded = set()  # Lưu danh sách các file đã tải
    print("Bắt đầu giám sát file input.txt. Nhấn Ctrl+C để dừng.")
    try:
        while True:
            # Đọc các file mới cần tải
            new_files = read_new_files(file_name, already_downloaded)
            if new_files:
                print(f"Các file mới cần tải: {new_files}")
            else:
                print("Không có File cần tải xuống!")




            for file in new_files:
                client.sendall(file.encode(FORMAT))
                time.sleep(1)
                response = client.recv(1024).decode(FORMAT)




                if response == "OK":
                    download_file(client, file)
                    time.sleep(2)
                elif response == "NOT_FOUND":
                    print(f"Không thể tải file '{file}'.")
                already_downloaded.add(file) # Đánh dấu file đã tải




            time.sleep(5)  # Chờ 5 giây trước khi quét lại
    except KeyboardInterrupt:
        print("\nDừng giám sát file.")
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")




def main():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))        
        client.sendall("CLIENT".encode(FORMAT))
        time.sleep(1)


        if not perform_handshake_client(client):
            print("Handshake thất bại với server.")
            return
       
        list_files = client.recv(1024).decode(FORMAT)
        print("Danh sách file từ server:")
        print(list_files)
        monitor(client, "input.txt")
    except Exception as e:
        print(f"Có lỗi khi kết nối đến server: {e}")
    finally:
        print("Client đã thoát.")


if __name__ == "__main__":
    main()



















































































































































































