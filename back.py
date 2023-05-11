import json
import os
import shutil
import hashlib
import requests
from datetime import datetime
import sys
import zipfile
import uuid
import ctypes
from tqdm import tqdm

# URL for downloading metadata
METADATA_URL = 'https://themea.eu.org/update/metadata.json'
# Name of the file with the game version
GAME_VERSION_FILE = 'gamever.txt'
# set user agent of requests
user_agent = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0'}
def load_game_version():
    try:
        with open(GAME_VERSION_FILE, 'r') as in_file:
            return int(in_file.read().strip())
    except FileNotFoundError as err:
        print(f"Failed to load game version. Error: {err}")
        sys.exit(1)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def download_file(url, filename):
    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)
            with open(filename, 'wb') as out_file:
                for chunk in response.iter_content(chunk_size=1024):
                    progress_bar.update(len(chunk))
                    out_file.write(chunk)
            progress_bar.close()
    except requests.RequestException as err:
        print(f"Failed to download file from {url}. Error: {err}")
        return False
    return True

def load_json(filename):
    try:
        with open(filename, 'r') as in_file:
            return json.load(in_file)
    except FileNotFoundError as err:
        print(f"Failed to load json file {filename}. Error: {err}")
        sys.exit(1)

def check_update(version, latest_version):
    return int(latest_version) > int(version)

def check_sha256(filename, sha256):
    with open(filename, 'rb') as in_file:
        file_sha256 = hashlib.sha256(in_file.read()).hexdigest()
    return file_sha256 == sha256

def unzip_file(filename, path):
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(path)

def replace_files(source_path, dest_path):
    # Iterate over all files in source directory
    for subdir, dirs, files in os.walk(source_path):
        for file in files:
            src_file_path = os.path.join(subdir, file)
            dst_file_path = os.path.join(dest_path, src_file_path.replace(source_path, ""))
            dst_file_dir = os.path.dirname(dst_file_path)
            
            # If destination directory does not exist, create it
            if not os.path.exists(dst_file_dir):
                os.makedirs(dst_file_dir)
            
            # Copy source file to destination directory
            shutil.copy2(src_file_path, dst_file_path)
def modify_hosts(ip, domain):
    hosts_file_path = r"C:\\Windows\\System32\\drivers\\etc\\hosts"
    backup_hosts_file_path = r"C:\\Windows\\System32\\drivers\etc\\hosts.backup"
    
    # Back up the original hosts file
    shutil.copyfile(hosts_file_path, backup_hosts_file_path)
    
    with open(hosts_file_path, 'a') as file:
        file.write(f"\n{ip} {domain}")
def restore_hosts():
    hosts_file_path = r"C:\\Windows\\System32\\drivers\\etc\\hosts"
    backup_hosts_file_path = r"C:\\Windows\\System32\\drivers\\etc\\hosts.backup"
    
    # Restore the original hosts file
    if os.path.exists(backup_hosts_file_path):
        shutil.copyfile(backup_hosts_file_path, hosts_file_path)
        os.remove(backup_hosts_file_path)

def update_self(metadata):
    if metadata['programneedupdate'].lower() == 'true':
        bat_filename = str(uuid.uuid4()) + '.bat'
        with open(bat_filename, 'w') as bat_file:
            bat_file.write("""
            @echo off
            timeout /t 5 /nobreak
            del updater.exe
            move bin\\updater.exe .
            del {}
            """.format(bat_filename))
        os.system(bat_filename)

if is_admin():
    metadata = load_json('metadata.json')
    #modify_hosts(metadata['1drvip'], "nyaamo-my.sharepoint.com")
    #modify_hosts(metadata['githubip'], "objects.githubusercontent.com")
    pass
else:
    # Re-run the program with admin rights
    # ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    # 下面这句没用，但是不加会报错
    block=0
def main():
    # Download and load metadata
    download_file(METADATA_URL, 'metadata.json')
    metadata = load_json('metadata.json')
    # Load local game version
    game_version = load_game_version()

   # Check for updates
    if not check_update(game_version, metadata['latestversioncode']):
        print("No new updates.")
        sys.exit(0)

    print("New update available. Downloading...")
    # Download the update
    update_file = metadata['updfilename']
    if not download_file(metadata['github'], update_file):
        print("Failed to download from OneDrive1. Trying OneDrive...")
        if not download_file(metadata['1drv'], update_file):
            print("Failed to download update. Exiting...")
            sys.exit(1)

    # Check the update package
    if not check_sha256(update_file, metadata['SHA256']):
        print("Update package integrity check failed.")
        sys.exit(1)
        # Extract the update
    unzip_file(update_file, './update')

    # Replace the old files with the new ones
    replace_files('update', '.')

# Update the local game version
    game_version = metadata['latestversioncode']
    with open(GAME_VERSION_FILE, 'w') as out_file:
        out_file.write(str(game_version))

    # Update the updater itself if needed
    update_self(metadata)
    #restore_hosts()
    print("Update complete.")

if __name__ == "__main__":
    main()
