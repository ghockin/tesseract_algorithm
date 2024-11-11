import os

def check_folder(output_directory):
    if os.path.exists(output_directory) and os.path.isdir(output_directory):
        for root, dirs, files in os.walk(output_directory, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                os.remove(file_path)
            for name in dirs:
                dir_path = os.path.join(root, name)
                os.rmdir(dir_path)
        os.rmdir(output_directory)
    
    os.makedirs(output_directory)