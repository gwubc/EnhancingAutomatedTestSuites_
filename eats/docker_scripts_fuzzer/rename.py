import os

directory = '/workplace/finial_pynguin_results'
for filename in os.listdir(directory):
    if filename.endswith('.py'):
        file_root, file_extension = os.path.splitext(filename)
        new_file_name = f"{file_root}_1{file_extension}"
        old_file_path = os.path.join(directory, filename)
        new_file_path = os.path.join(directory, new_file_name)
        os.rename(old_file_path, new_file_path)
        print(f"Renamed {filename} to {new_file_name}")
