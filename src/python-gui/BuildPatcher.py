import tkinter as tk
from tkinter import messagebox, filedialog
from threading import Thread
import configparser
import hashlib
import os
import psutil
import sys
import time
import webbrowser
import subprocess
import threading
from threading import Thread

class PatcherGUI:
    def __init__(self, master):
        self.master = master
        self.info_label = tk.Label(master, text="", fg="green")
        self.info_label.pack()

        left_frame = tk.Frame(self.master)
        left_frame.pack(side=tk.LEFT, padx=5)

        right_frame = tk.Frame(self.master)
        right_frame.pack(side=tk.RIGHT, padx=5)

        bottom_frame = tk.Frame(self.master)
        bottom_frame.pack(side=tk.BOTTOM, pady=10)
        
        help_button = tk.Frame(self.master)
        help_button.pack(side=tk.TOP, padx=5)
        
        self.create_button(help_button, "HELP", self.open_help_link,
                   "This will open the github readme file to explain this app's uses and warnings.")
        
        self.create_button(left_frame, "Permanent Client Patch", lambda: self.execute_patch("Permanent_Client"),
                           "This will create a backup of the game's executable file and apply the patches. Afterward, you can close this program and run the game yourself.\n\nWARNING: This method may make it easy to overlook game updates, potentially leading to accidentally launching the game without the patches and risking your base if you used the Build without support option.")
        self.create_button(left_frame, "Temporary Client Patch", lambda: self.execute_patch("Temporary_Client"),
                           "This will create a backup of the game's executable file, apply the patches, launch the game, and after the game is closed it will restore the game's executable using the previously made backup.")
        self.create_button(right_frame, "Permanent Server Patch", lambda: self.execute_patch("Permanent_Server"),
                           "This will create a backup of the server's executable file and apply the patches. Afterward, you can close this program and run the game yourself.\n\nWARNING: This method may make it easy to overlook server updates, potentially leading to accidentally launching the server without the patches and risking your base if you used the Build without support option.")
        self.create_button(right_frame, "Temporary Server Patch", lambda: self.execute_patch("Temporary_Server"),
                           "This will create a backup of the server's executable file, apply the patches, launch the server, and after the server is closed it will restore the server's executable using the previously made backup.")

        self.create_button(bottom_frame, "Restore EXE", lambda: self.execute_patch("Restore"),
                           "This will restore the EXE files from the backups made by the other Permanent options if needed.")

        self.info_popup = None
    
    def execute_patch_from_command_line(self, arg):
        valid_args = ["Permanent_Client", "Temporary_Client", "Permanent_Server", "Temporary_Server", "Restore"]

        if arg not in valid_args:
            print("Invalid argument. Please provide one of the following: {}".format(valid_args))
            return

        self.execute_script(arg)
    
    def open_help_link(self):
        webbrowser.open("https://raw.githubusercontent.com/Spark-NV/Palworld-DisableBuildingRestrictions/master/Patcher/Instructions.txt")

    def create_button(self, frame, text, command, popup_message):
        button = tk.Button(frame, text=text, command=command)
        button.pack(side=tk.TOP, pady=10)
        button.bind("<Enter>", lambda event, msg=popup_message: self.show_info_popup(event, msg))
        button.bind("<Leave>", self.hide_info_popup)
        
    def create_dual_buttons(self, text1, command1, popup_message1, text2, command2, popup_message2):
        frame = tk.Frame(self.master)
        frame.pack()

        self.create_button(text1, lambda: self.execute_patch(command1), popup_message1)
        self.create_button(text2, lambda: self.execute_patch(command2), popup_message2)


    def hide_info_popup(self, _):
        if self.info_popup:
            self.info_popup.destroy()
            self.info_popup = None

    def show_info_popup(self, event, message):
        x, y, _, _ = event.widget.bbox("insert")
        x += event.widget.winfo_rootx() + 25
        y += event.widget.winfo_rooty() + 25

        self.info_popup = tk.Toplevel(event.widget)
        self.info_popup.wm_overrideredirect(True)
        self.info_popup.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.info_popup, text=message, justify='left', background="#ffffff", relief='solid', borderwidth=1, wraplength=250)
        label.pack(ipadx=1)

    def set_info_message(self, message):
        self.info_label.config(text=message)

    @staticmethod
    def hex_string_to_bytes(hex_string):
        return bytes.fromhex(hex_string)

    @staticmethod
    def replace_hex_pattern(file_content, search_hex, replace_hex):
        search_bytes = PatcherGUI.hex_string_to_bytes(search_hex)
        replace_bytes = PatcherGUI.hex_string_to_bytes(replace_hex)

        index = file_content.find(search_bytes)
        while index != -1:
            file_content = file_content[:index] + replace_bytes + file_content[index + len(search_bytes):]
            index = file_content.find(search_bytes)

        return file_content

    @staticmethod
    def calculate_sha256(file_content):
        sha256 = hashlib.sha256()
        sha256.update(file_content)
        return sha256.hexdigest()

    def read_hex_edits_from_ini(self, file_path, is_client_or_server):
        config = configparser.ConfigParser()
        config.read(file_path)
        hex_edits = {}
    
        for section in config.sections():
            if section != 'SHA256' and section != 'ROOT':
                if is_client_or_server == 'Permanent_Client':
                    if 'ClientSearch' in config[section] and 'ClientReplace' in config[section]:
                        search_hex = config[section]['ClientSearch']
                        replace_hex = config[section]['ClientReplace']
                        hex_edits[section] = {'search': search_hex, 'replace': replace_hex}
                    else:
                        print(f"Warning: Section '{section}' is missing 'Search' or 'Replace' key. Skipping.")
                elif is_client_or_server == 'Permanent_Server':
                    if 'ServerSearch' in config[section] and 'ServerReplace' in config[section]:
                        search_hex = config[section]['ServerSearch']
                        replace_hex = config[section]['ServerReplace']
                        hex_edits[section] = {'search': search_hex, 'replace': replace_hex}
                    else:
                        print(f"Warning: Section '{section}' is missing 'Search' or 'Replace' key. Skipping.")
                elif is_client_or_server == 'Temporary_Client':
                    if 'ClientSearch' in config[section] and 'ClientReplace' in config[section]:
                        search_hex = config[section]['ClientSearch']
                        replace_hex = config[section]['ClientReplace']
                        hex_edits[section] = {'search': search_hex, 'replace': replace_hex}
                    else:
                        print(f"Warning: Section '{section}' is missing 'Search' or 'Replace' key. Skipping.")
                elif is_client_or_server == 'Temporary_Server':
                    if 'ServerSearch' in config[section] and 'ServerReplace' in config[section]:
                        search_hex = config[section]['ServerSearch']
                        replace_hex = config[section]['ServerReplace']
                        hex_edits[section] = {'search': search_hex, 'replace': replace_hex}
                    else:
                        print(f"Warning: Section '{section}' is missing 'Search' or 'Replace' key. Skipping.")
                else:
                    print("this shouldnt happen.")
    
        return hex_edits

    def read_expected_sha256_from_ini(self, file_path, is_client_or_server):
        config = configparser.ConfigParser()
        config.read(file_path)
        if is_client_or_server == 'Permanent_Client':
            return config['SHA256']['ClientExpected']
        elif is_client_or_server == 'Temporary_Client':
            return config['SHA256']['ClientExpected']
        elif is_client_or_server == 'Permanent_Server':
            return config['SHA256']['ServerExpected']
        elif is_client_or_server == 'Temporary_Server':
            return config['SHA256']['ServerExpected']
        else:
            print("this shouldnt happen.")

    def monitor_game_process(self, process_names, cleanup_function, *args):
        time.sleep(5)
        while True:
            if any(process_name in [p.name() for p in psutil.process_iter(['name'])] for process_name in process_names):
                time.sleep(5)
            else:
                cleanup_function(*args)
                break
                
    def monitor_server_process(self, process_names, cleanup_function, *args):
        time.sleep(5)
        while True:
            if any(process_name in [p.name() for p in psutil.process_iter(['name'])] for process_name in process_names):
                time.sleep(5)
            else:
                cleanup_function(*args)
                break
    
    def clientcleanup(self, cfile_path, cbackup_file_path):
        try:
            os.remove(cfile_path)
            os.rename(cbackup_file_path, cfile_path)
            print("Game client closed!\n\nThe exe has been restored.")
            self.set_info_message("Game client closed!\n\nThe exe has been restored.")
        except Exception as e:
            print("")
    
    def servercleanup(self, sfile_path, sbackup_file_path):
        try:
            os.remove(sfile_path)
            os.rename(sbackup_file_path, sfile_path)
            print("Server closed!\n\nThe exe has been restored.")
            self.set_info_message("Server exe closed!\n\nThe exe has been restored.")
        except Exception as e:
            print("")

    def execute_script(self, is_client_or_server):
        try:
            ini_file_path = "BuildPatcher.ini"
            if not os.path.exists(ini_file_path):
                messagebox.showerror("!! Error !!, Cannot find BuildPatcher.ini",
                                     "Please make sure the BuildPatcher.ini file is present and in the same directory as this Exe")
                return
            config = configparser.ConfigParser()
            config.read(ini_file_path)

            if is_client_or_server == 'Permanent_Client':
                palworld_root = config['ROOT']['palworld_root']
                exe_name = os.path.join(palworld_root, "Palworld.exe")
                file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping.exe")
                backup_file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping_backup.exe")
            elif is_client_or_server == 'Permanent_Server':
                palserver_root = config['ROOT']['palserver_root']
                exe_name = os.path.join(palserver_root, "PalServer.exe")
                file_path = os.path.join(palserver_root, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd.exe")
                backup_file_path = os.path.join(palserver_root, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd_backup.exe")
            elif is_client_or_server == 'Temporary_Client':
                palworld_root = config['ROOT']['palworld_root']
                exe_name = os.path.join(palworld_root, "Palworld.exe")
                file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping.exe")
                backup_file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping_backup.exe")
                cfile_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping.exe")
                cbackup_file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping_backup.exe")
            elif is_client_or_server == 'Temporary_Server':
                palserver_root = config['ROOT']['palserver_root']
                exe_name = os.path.join(palserver_root, "PalServer.exe")
                file_path = os.path.join(palserver_root, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd.exe")
                backup_file_path = os.path.join(palserver_root, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd_backup.exe")
                sfile_path = os.path.join(palserver_root, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd.exe")
                sbackup_file_path = os.path.join(palserver_root, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd_backup.exe")
            elif is_client_or_server == 'Restore':
                palserver_root = config['ROOT']['palserver_root']
                palworld_root = config['ROOT']['palworld_root']
                #exe_name = os.path.join(palserver_root, "PalServer.exe")
                server_file_path = os.path.join(palserver_root, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd.exe")
                server_backup_file_path = os.path.join(palserver_root, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd_backup.exe")
                client_file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping.exe")
                client_backup_file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping_backup.exe")
            else:
                print("Error: weird, this shouldn't happen.")

            if is_client_or_server != "Restore":
                if not os.path.exists(file_path):
                    messagebox.showerror("\nError: The file {} does not exist. Please ensure palworld_root is set correctly in the INI file.\n".format(file_path))
                    return
                with open(file_path, 'rb') as file:
                    original_content = file.read()

                expected_sha256 = self.read_expected_sha256_from_ini(ini_file_path, is_client_or_server)
                original_sha256 = self.calculate_sha256(original_content)
                print(f"Original SHA256: {original_sha256}")

                if original_sha256 != expected_sha256:
                    messagebox.showerror("!!!!!! WARNING !!!!!!",
                                         f"SHA256 hash does not match. Game version is either wrong or something has happened to your games exe.\n\nEither restore the games EXE from the backup or wait for an update to the patcher.\n\nNote: this patcher only supports palworld 0.1.4.1")
                    return

                with open(backup_file_path, 'wb') as backup_file:
                    backup_file.write(original_content)

                hex_edits = self.read_hex_edits_from_ini(ini_file_path, is_client_or_server)

                for edit_name, edit_data in hex_edits.items():
                    search_hex = edit_data["search"]
                    replace_hex = edit_data["replace"]
                    original_content = self.replace_hex_pattern(original_content, search_hex, replace_hex)

                with open(file_path, 'wb') as modified_file:
                    modified_file.write(original_content)

            if is_client_or_server == "Temporary_Client":
                self.set_info_message("Temporary Client patch completed successfully!\n\nThe game will now launch.")

                time.sleep(2)
                subprocess.Popen(["start", "steam://rungameid/1623730"], shell=True)
                threading.Thread(target=self.monitor_game_process, args=[("Palworld-Win64-Shipping.exe", "Palworld.exe"), self.clientcleanup, cfile_path, cbackup_file_path]).start()
            elif is_client_or_server == "Temporary_Server":
                self.set_info_message("Temporary Server patch completed successfully!\n\nThe server will now launch.")
                time.sleep(2)
                subprocess.Popen(["start", "steam://rungameid/2394010"], shell=True)
                threading.Thread(target=self.monitor_server_process, args=[("PalServer-Win64-Test-Cmd.exe", "Palserver.exe"), self.servercleanup, sfile_path, sbackup_file_path]).start()
            elif is_client_or_server == "Permanent_Client":
                self.set_info_message("Permanent Client patch completed successfully!\nA backup of the exe will be stored here:\n{}".format(backup_file_path))
            elif is_client_or_server == "Permanent_Server":
                self.set_info_message("Permanent Server patch completed successfully!\nA backup of the exe will be stored here:\n{}".format(backup_file_path))
                
            elif is_client_or_server == "Restore":
                if not os.path.exists(client_backup_file_path) and not os.path.exists(server_backup_file_path):
                    messagebox.showerror("Error",
                             "It appears there is no backup file present to use.\n\nThis option restores the backup files.\n\nIf they are not present or renamed, this will not work.")
                if os.path.exists(client_backup_file_path):
                    os.remove(client_file_path)
                    os.rename(client_backup_file_path, client_file_path)
                    self.set_info_message("EXE has been restored using the client backup file manually.")
                if os.path.exists(server_backup_file_path):
                    os.remove(server_file_path)
                    os.rename(server_backup_file_path, server_file_path)
                    self.set_info_message("EXE has been restored using the server backup file manually.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def execute_patch(self, is_client_or_server):
        self.set_info_message("Working!")
        Thread(target=lambda: self.execute_script(is_client_or_server)).start()


if __name__ == "__main__":
    root = tk.Tk()
    gui = PatcherGUI(root)
    root.title("Palworld Build Restrictions Remover Patcher")

    if len(sys.argv) == 2:
        gui.execute_patch_from_command_line(sys.argv[1])
    else:
        def update_window_size():
            root.update_idletasks()
            width = root.winfo_reqwidth()
            height = root.winfo_reqheight()
            root.geometry(f"{width}x{height}")

        root.minsize(400, 100)
        root.mainloop()