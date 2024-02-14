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
import webbrowser

def should_perform_cleanup(ini_file_path):
    config = configparser.ConfigParser()
    config.read(ini_file_path)
    cleanup_section = config['PERMANENT PATCH']
    return cleanup_section.get('patch_is_permanent', 'true').lower() == 'true'

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

def read_hex_edits_from_ini(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    hex_edits = {}

    for section in config.sections():
        if section != 'SHA256' and section != 'ROOT':
            if 'Search' in config[section] and 'Replace' in config[section]:
                search_hex = config[section]['Search']
                replace_hex = config[section]['Replace']
                hex_edits[section] = {'search': search_hex, 'replace': replace_hex}
            else:
                print(f"Warning: Section '{section}' is missing 'Search' or 'Replace' key. Skipping.")

    return hex_edits

def read_expected_sha256_from_ini(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config['SHA256']['Expected']

def cleanup(file_path, backup_file_path):
    while True:
        processes = [p.name() for p in psutil.process_iter(['pid', 'name'])]
        
        if "palworld.exe" in processes or "Palworld-Win64-Shipping.exe" in processes:
            time.sleep(5)
        else:
            print("Game closed!")

            os.remove(file_path)
            os.rename(backup_file_path, file_path)

            print("\nDirectory cleaned and restored.\n")
            
            break

def main():
    ini_file_path = "BuildPatcher.ini"
    
    perform_cleanup = should_perform_cleanup(ini_file_path)
    config = configparser.ConfigParser()
    config.read(ini_file_path)

    palworld_root = config['ROOT']['palworld_root']
    exe_name = os.path.join(palworld_root, "Palworld.exe")
    file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping.exe")
    backup_file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping_backup.exe")

    if not os.path.exists(file_path):
        print(f"\nError: The file '{file_path}' does not exist. Please ensure palworld_root is set correctly in the INI file.\n")
        input("Press any key to exit...")
        exit(1)

    with open(file_path, 'rb') as file:
        original_content = file.read()

    expected_sha256 = read_expected_sha256_from_ini(ini_file_path)
    original_sha256 = calculate_sha256(original_content)
    print(f"Original SHA256: {original_sha256}")

    if original_sha256 != expected_sha256:
        print("\nError: SHA256 hash does not match. Game version is either wrong or some mods are already applied. Exiting.\n")
        input("Press any key to exit...")
        return

    with open(backup_file_path, 'wb') as backup_file:
        backup_file.write(original_content)

    hex_edits = read_hex_edits_from_ini(ini_file_path)

    for edit_name, edit_data in hex_edits.items():
        search_hex = edit_data["search"]
        replace_hex = edit_data["replace"]
        original_content = replace_hex_pattern(original_content, search_hex, replace_hex)
        print(f"Applied hex edit: {edit_name}")

    with open(file_path, 'wb') as modified_file:
        modified_file.write(original_content)

    print("Mods applied successfully.")
    if not perform_cleanup:
        print("\nTemp patch enabled. Exe will be patched then restore when game closes.\n")
        webbrowser.open("steam://rungameid/1623730")
        time.sleep(5)
        cleanup(file_path, backup_file_path)
    else:
        print(f"\nPermanent patch enabled. Exe is now patched until an update happens. A backup is still here: {backup_file_path} and can be restored if needed.\n")
        input("Press any key to exit...")

if __name__ == "__main__":
    main()
