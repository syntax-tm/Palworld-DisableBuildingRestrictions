import tkinter as tk
from tkinter import messagebox, filedialog
from threading import Thread
import configparser
import hashlib
import os
import psutil
import time
import webbrowser

class PatcherGUI:
    def __init__(self, master):
        self.master = master
        self.info_label = tk.Label(master, text="", fg="green")
        self.info_label.pack()

        self.create_button("Temporary Patch", lambda: self.execute_patch("Temporary"),
                           "This will create a backup of the game's executable file, apply the patches, launch the game, and after the game is closed it will restore the game's executable using the previously made backup.")
        self.create_button("Permanent Patch", lambda: self.execute_patch("Permanent"),
                           "This will create a backup of the game's executable file and apply the patches. Afterward, you can close this program and run the game yourself.\n\nWARNING: This method may make it easy to overlook game updates, potentially leading to accidentally launching the game without the patches and risking your base if you used the Build without support option.")
        self.create_button("Restore EXE", lambda: self.execute_patch("Restore"),
                           "This will restore the EXE from the backup made by the other 2 options if needed.")

        self.info_popup = None

    def create_button(self, text, command, popup_message):
        button = tk.Button(self.master, text=text, command=command)
        button.pack(pady=10)
        button.bind("<Enter>", lambda event, msg=popup_message: self.show_info_popup(event, msg))
        button.bind("<Leave>", self.hide_info_popup)

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

    def read_hex_edits_from_ini(self, file_path):
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

    def read_expected_sha256_from_ini(self, file_path):
        config = configparser.ConfigParser()
        config.read(file_path)
        return config['SHA256']['Expected']

    def cleanup(self, file_path, backup_file_path):
        while True:
            processes = [p.name() for p in psutil.process_iter(['pid', 'name'])]

            if "palworld.exe" in processes or "Palworld-Win64-Shipping.exe" in processes:
                self.set_info_message("Game Running. with mods applied")
                time.sleep(5)
            else:
                os.remove(file_path)
                os.rename(backup_file_path, file_path)
                self.set_info_message("Game closed. Exe Restored...")
                break

    def execute_script(self, patch_type):
        try:
            ini_file_path = "BuildPatcher.ini"
            if not os.path.exists(ini_file_path):
                messagebox.showerror("!! Error !!, Cannot find BuildPatcher.ini",
                                     "Please make sure the BuildPatcher.ini file is present and in the same directory as this Exe")
                return
            config = configparser.ConfigParser()
            config.read(ini_file_path)

            palworld_root = config['ROOT']['palworld_root']
            exe_name = os.path.join(palworld_root, "Palworld.exe")
            file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64", "Palworld-Win64-Shipping.exe")
            backup_file_path = os.path.join(palworld_root, "Pal", "Binaries", "Win64",
                                            "Palworld-Win64-Shipping_backup.exe")

            if patch_type != "Restore":
                if not os.path.exists(file_path):
                    messagebox.showerror("\nError: The file {} does not exist. Please ensure palworld_root is set correctly in the INI file.\n".format(file_path))
                    return
                with open(file_path, 'rb') as file:
                    original_content = file.read()

                expected_sha256 = self.read_expected_sha256_from_ini(ini_file_path)
                original_sha256 = self.calculate_sha256(original_content)
                print(f"Original SHA256: {original_sha256}")

                if original_sha256 != expected_sha256:
                    messagebox.showerror("!!!!!! WARNING !!!!!!",
                                         f"SHA256 hash does not match. Game version is either wrong or something has happened to your games exe.\n\nEither restore the games EXE from the backup or wait for an update to the patcher.\n\nNote: this patcher only supports palworld 0.1.4.1")
                    return

                with open(backup_file_path, 'wb') as backup_file:
                    backup_file.write(original_content)

                hex_edits = self.read_hex_edits_from_ini(ini_file_path)

                for edit_name, edit_data in hex_edits.items():
                    search_hex = edit_data["search"]
                    replace_hex = edit_data["replace"]
                    original_content = self.replace_hex_pattern(original_content, search_hex, replace_hex)

                with open(file_path, 'wb') as modified_file:
                    modified_file.write(original_content)

            if patch_type == "Temporary":
                self.set_info_message("Temporary patch completed successfully!\n\nThe game will now launch.")
                time.sleep(2)
                Thread(target=lambda: webbrowser.open("steam://rungameid/1623730")).start()
                self.master.after(5000, lambda: self.cleanup(file_path, backup_file_path))
            elif patch_type == "Permanent":
                self.set_info_message("Permanent patch completed successfully!\nA backup of the exe will be stored here:\n{}".format(backup_file_path))
            elif patch_type == "Restore":
                if os.path.exists(backup_file_path):
                    os.remove(file_path)
                    os.rename(backup_file_path, file_path)
                    self.set_info_message("EXE has been restored using the backup file manually.")
                else:
                    messagebox.showerror("Error",
                                         "It appears there is no backup file present to use\n\n this option restores the file:\n\n {}\n\nif it's not present or renamed this will not work.".format(
                                             backup_file_path))

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def execute_patch(self, patch_type):
        Thread(target=lambda: self.execute_script(patch_type)).start()


if __name__ == "__main__":
    root = tk.Tk()
    gui = PatcherGUI(root)
    root.title("Palworld Build Restrictions Remover Patcher")

    def update_window_size():
        root.update_idletasks()
        width = root.winfo_reqwidth()
        height = root.winfo_reqheight()
        root.geometry(f"{width}x{height}")
    root.minsize(400, 100)
    root.mainloop()
