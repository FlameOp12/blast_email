import base64
import sys

def encode_file_to_base64(file_path):
    with open(file_path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(encode_file_to_base64(file_path))