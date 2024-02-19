import importlib

def install_module(module_name):
    try:
        importlib.import_module(module_name)
        print(f"{module_name} is already installed. This is good.")
    except ImportError:
        print(f"{module_name} is not installed. Installing...")
        try:
            import subprocess
            subprocess.check_call(['pip', 'install', module_name])
            print(f"{module_name} has been successfully installed.")
        except Exception as e:
            print(f"Error installing {module_name}: {e}")
            input("Press any key to exit...")

modules_to_check = ['configparser', 'hashlib', 'os', 'psutil', 'time', 'webbrowser']
for module_name in modules_to_check:
    install_module(module_name)

import configparser
import hashlib
import os
import psutil
import time
import subprocess
import sys
import webbrowser
import threading
from threading import Thread


def get_user_input():
    while True:
        if len(sys.argv) > 1:
            arg = sys.argv[1]
            if arg.isdigit() and 1 <= int(arg) <= 5:
                return [arg]
            else:
                print("Invalid command line argument. Please provide a number from 1 to 4.")
                sys.exit(1)
    
        print("\n\nWhat do you want to patch?")
        print("\n1. Patch the Client, Permanently (ie:Create a backup then patch the exe.)")
        print("2. Patch the Client, Temporarily (ie:Patches, then launches the game, will restore the games exe after closing")
        print("\n3. Patch the Server, Permanently (ie:Create a backup then patch the exe.")
        print("4. Patch the Server, Temporarily (ie:Patches, then launches the server, will restore the exe after closing")
        print("\n5. Patch BOTH the Server and Client, Temporarily (ie:Patches, then launches the server plus the client, will restore both exe after closing\n")

        user_input = input("Enter the corresponding numbers (1/2/3/4/5): ")

        try:
            if user_input == '5':
                return ['5']
            elif user_input in ('1', '2', '3', '4'):
                return [user_input]
            else:
                print("Invalid input. Please enter a number from the list above.")
        except ValueError:
            print("Invalid input. Please enter a number from the list above.")
        

def hex_string_to_bytes(hex_string):
    return bytes.fromhex(hex_string)

def replace_hex_pattern(file_content, search_hex, replace_hex):
    search_bytes = hex_string_to_bytes(search_hex)
    replace_bytes = hex_string_to_bytes(replace_hex)

    index = file_content.find(search_bytes)
    while index != -1:
        file_content = file_content[:index] + replace_bytes + file_content[index + len(search_bytes):]
        index = file_content.find(search_bytes)

    return file_content

def calculate_sha256(file_content):
    sha256 = hashlib.sha256()
    sha256.update(file_content)
    return sha256.hexdigest()

def read_hex_edits_from_ini(file_path, is_client_or_server):
    config = configparser.ConfigParser()
    config.read(file_path)
    hex_edits = {}

    for section in config.sections():
        if section != 'SHA256' and section != 'ROOT':
            if is_client_or_server == 'client':
                if 'ClientSearch' in config[section] and 'ClientReplace' in config[section]:
                    search_hex = config[section]['ClientSearch']
                    replace_hex = config[section]['ClientReplace']
                    hex_edits[section] = {'search': search_hex, 'replace': replace_hex}
                else:
                    print(f"Warning: Section '{section}' is missing 'Search' or 'Replace' key. Skipping.")
            elif is_client_or_server == 'server':
                if 'ServerSearch' in config[section] and 'ServerReplace' in config[section]:
                    search_hex = config[section]['ServerSearch']
                    replace_hex = config[section]['ServerReplace']
                    hex_edits[section] = {'search': search_hex, 'replace': replace_hex}
                else:
                    print(f"Warning: Section '{section}' is missing 'Search' or 'Replace' key. Skipping.")
            else:
                print("Error: 'is_client_or_server' is not set to 'client' or 'server'. Please check the ini file.")
                input("Press any key to exit...")
                exit(1)

    return hex_edits

def read_expected_sha256_from_ini(file_path, is_client_or_server):
    config = configparser.ConfigParser()
    config.read(file_path)
    if is_client_or_server == 'client':
        return config['SHA256']['ClientExpected']
    elif is_client_or_server == 'server':
        return config['SHA256']['ServerExpected']
    else:
        print("Error: 'is_client_or_server' is not set to 'client' or 'server'. Please check the ini file.")
        input("Press any key to exit...")
        exit(1)

def monitor_game_process(process_names, cleanup_function, *args):
    while True:
        if any(process_name in [p.name() for p in psutil.process_iter(['name'])] for process_name in process_names):
            time.sleep(5)
        else:
            cleanup_function(*args)
            break
            
def monitor_server_process(process_names, cleanup_function, *args):
    while True:
        if any(process_name in [p.name() for p in psutil.process_iter(['name'])] for process_name in process_names):
            time.sleep(5)
        else:
            cleanup_function(*args)
            break

def clientcleanup(cfile_path, cbackup_file_path):
    try:
        os.remove(cfile_path)
        os.rename(cbackup_file_path, cfile_path)
        print("Game client closed!\n\nThe exe has been restored.")
    except Exception as e:
        print(f"Error during client cleanup: {e}")

def servercleanup(sfile_path, sbackup_file_path):
    try:
        os.remove(sfile_path)
        os.rename(sbackup_file_path, sfile_path)
        print("Server closed!\n\nThe exe has been restored.")
    except Exception as e:
        print(f"Error during server cleanup: {e}")

def main():
    ini_file_path = "BuildPatcher.ini"
    config = configparser.ConfigParser()
    config.read(ini_file_path)
    user_input = get_user_input()
    print(f"User input: {user_input}")
    
    if user_input and '5' in user_input:
        patch_is_permanent = 'false'
        is_client_or_server = 'client'
        subprocess.Popen(['python', 'BuildPatcher.py', '4'], creationflags=subprocess.CREATE_NO_WINDOW)
    elif user_input and user_input[0] in ('1', '2', '3', '4'):
        patch_is_permanent = 'true' if user_input[0] in ('1', '3') else 'false'
        is_client_or_server = 'client' if user_input[0] in ('1', '2') else 'server'
    # Perform patching logic for the selected option (client or server) here
    else:
        print("Invalid input. Please enter 1, 2, 3, 4, or 5.")

    
    
    if is_client_or_server == 'client':
        palworld_root = config['ROOT']['palworld_root']
        exe_name = os.path.join(palworld_root, "Palworld.exe")
        file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping.exe")
        backup_file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping_backup.exe")
        cfile_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping.exe")
        cbackup_file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping_backup.exe")
    
    elif is_client_or_server == 'server':
        palserver_root = config['ROOT']['palserver_root']
        exe_name = os.path.join(palserver_root, "PalServer.exe")
        file_path = os.path.join(palserver_root, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd.exe")
        backup_file_path = os.path.join(palserver_root, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd_backup.exe")
        sfile_path = os.path.join(palserver_root, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd.exe")
        sbackup_file_path = os.path.join(palserver_root, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd_backup.exe")
        
                
    else:
        print("Error: weird, this shouldn't happen.")
        input("Press any key to exit...")
        exit(1)
    

    if file_path and not os.path.exists(file_path):
        print(f"\nError: The file '{file_path}' does not exist. Please ensure palworld_root and/or palserver_root is set correctly in the INI file.\n")
        input("Press any key to exit...")
        exit(1)

    with open(file_path, 'rb') as file:
        original_content = file.read()

    expected_sha256 = read_expected_sha256_from_ini(ini_file_path, is_client_or_server)
    original_sha256 = calculate_sha256(original_content)
    print(f"Original SHA256: {original_sha256}")

    if original_sha256 != expected_sha256:
        print("\nError: SHA256 hash does not match. Game version is either wrong or some mods are already applied. Exiting.\n")
        input("Press any key to exit...")
        return

    with open(backup_file_path, 'wb') as backup_file:
        backup_file.write(original_content)

    hex_edits = read_hex_edits_from_ini(ini_file_path, is_client_or_server)

    for edit_name, edit_data in hex_edits.items():
        search_hex = edit_data["search"]
        replace_hex = edit_data["replace"]
        original_content = replace_hex_pattern(original_content, search_hex, replace_hex)
        print(f"Applied hex edit: {edit_name}")

    with open(file_path, 'wb') as modified_file:
        modified_file.write(original_content)

    print("Mods applied successfully.")
    if patch_is_permanent == 'false':
        if is_client_or_server == 'server':
            print("\nTemp patch enabled for server. Exe will be patched then restored when the game closes.\n")
            webbrowser.open("steam://rungameid/2394010")
            time.sleep(5)
            threading.Thread(target=monitor_game_process, args=[("PalServer-Win64-Test-Cmd.exe", "Palserver.exe"), servercleanup, sfile_path, sbackup_file_path]).start()
        elif is_client_or_server == 'client':
            print("\nTemp patch enabled for client. Exe will be patched then restored when the game closes.\n")
            webbrowser.open("steam://rungameid/1623730")
            time.sleep(5)
            threading.Thread(target=monitor_server_process, args=[("Palworld-Win64-Shipping.exe", "Palworld.exe"), clientcleanup, cfile_path, cbackup_file_path]).start()
            
        
    
    else:
        print(f"\nPermanent patch enabled. Exe is now patched until an update happens. A backup is still here: {backup_file_path} and can be restored if needed.\n")
        #input("Press any key to exit...")

if __name__ == "__main__":
    main()
