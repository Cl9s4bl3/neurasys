#News: --nowindow operator, changedir to a file

import readline
import os
import json
import subprocess
import ctypes
import sys

import requests
from urllib.parse import urlparse
import tqdm
import time as tm

from colorama import Fore, Style, init
from win32process import CREATE_NEW_CONSOLE

init()

import tempfile
import shutil
import psutil
import win32file

import platform

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL

import zipfile

hostname = platform.node()


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        print("This script requires administrative privileges. Trying to restart as administrator...")
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([script] + sys.argv[1:])
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        except Exception as e:
            print(f"Failed to elevate privileges. Check the logs to identify the issue.")
        sys.exit(0)

run_as_admin()

settings_dir = "C:\\Windows\\System32\\settings"
settings_json = "settings.json"
version_json = "version.json"

translations_file = os.path.join(settings_dir, "translations.json")

currentDirectory = "C:\\Windows\\System32\\root\\"

currentGroup = ""

current_language = None

ava_lang_short = {"English": "en-us", "German": "de-de", "Russian": "ru-ru"}

def set_console_title(title):
    ctypes.windll.kernel32.SetConsoleTitleW(title)

set_console_title("NeuraSys")

def safe_write_json(file_path, data, temp_name="NeuraSys"):
    try:
        temp_dir = os.path.dirname(file_path)
        temp_file_path = os.path.join(temp_dir, f"{temp_name}.tmp")

        with open(temp_file_path, 'w') as temp_file_handle:
            json.dump(data, temp_file_handle)
            temp_file_handle.flush()
            os.fsync(temp_file_handle.fileno())

        shutil.move(temp_file_path, file_path)

    except Exception as e:
        print(f"SAFE_WRITE_JSON ERROR: {e}")

translations_exe_path = "C:\\Windows\\System32\\translations.exe"
translations_json_path = os.path.join(settings_dir, "translations.json")


def load_translations(retry=False):

    try:
        global current_language

        if retry:
            print(f"Failed to load translation data, recreating neccessary files...\n")
            subprocess.run([translations_exe_path], check=True)

        if not os.path.exists(translations_json_path):
            print(f"Loading translations...\n")
            subprocess.run([translations_exe_path], check=True)


        with open(translations_json_path, 'r', encoding='utf-8') as trans_file:
            translations = json.load(trans_file)

        if translations.get("firstRun", "true").lower() == "true":
            print("Available languages:")
            for language in ava_lang_short:
                print(language, end="    ")

            while True:
                language = input("\n\nChoose a language from above: ").capitalize()
                if language not in ava_lang_short:
                    print("Invalid language. Try again.")
                else:
                    lan_code = ava_lang_short[language]
                    current_language = lan_code
                    translations["firstRun"] = "false"
                    translations["language"] = lan_code
                    break

            with open(translations_json_path, 'w', encoding='utf-8') as file:
                json.dump(translations, file)

        else:
            current_language = translations.get("language", "en-us")

    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        load_translations(retry=True)

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(f"Unexpected error: {e}")

def translate(key, **kwargs):
    try:
        lan = current_language

        with open(translations_json_path, 'r', encoding='utf-8') as translation_file:
            data = json.load(translation_file)

        if key not in data["translations"].get(lan, {}):
            return f"This translation does not exist in language '{current_language}'. Please contact a developer!"
        else:
            return data["translations"][lan][key].format(**kwargs)
    except Exception as e:
        print(f"Translation error: {e}")
        return f"Error retrieving translation for key '{key}'."

load_translations()


commands = {
    'help': {
        'description': translate("help_command"),
        'function': lambda: help_func()
    },
    'time': {
        'description': translate("time_command"),
        'function': lambda: show_time()
    },
    'list': {
        'description': translate("list_command"),
        'function': lambda: list_items()
    },
    'update': {
        'description': translate("update_command"),
        'function': lambda: updateMenu()
    },
    'create': {
        'description': translate("create_command"),
        'function': lambda: create()
    },
    'delete': {
        'description': translate("delete_command"),
        'function': lambda: delete()
    },
    'read': {
        'description': translate("read_command"),
        'function': lambda: read()
    },
    'openimg': {
        'description': translate("openimg_command"),
        'function': lambda: openIMG()
    },
    'openmp': {
        'description': translate("openmp_command"),
        'function': lambda: openMP()
    },
    'edit': {
        'description': translate("edit_command"),
        'function': lambda: edit()
    },
    'rename': {
        'description': translate("rename_command"),
        'function': lambda: rename()
    },
    'run': {
        'description': translate("run_command"),
        'function': lambda: run()
    },
    'download': {
        'description': translate("download_command"),
        'function': lambda: download()
    },
    'copy': {
        'description': translate("copy_command"),
        'function': lambda: copy()
    },
    'compress': {
        'description': translate("compress_command"),
        'function': lambda: compress()
    },
    'createdir': {
        'description': translate("createdir_command"),
        'function': lambda: createDir()
    },
    'deletedir': {
        'description': translate("deletedir_command"),
        'function': lambda: deleteDir()
    },
    'changedir': {
        'description': translate("changedir_command"),
        'function': lambda: changeDir()
    },
    'backdir': {
        'description': translate("backdir_command"),
        'function': lambda: backDir()
    },
    'currentdir': {
        'description': translate("currentdir_command"),
        'function': lambda: print(translate("current_dir"), currentDirectory.replace("C:\\Windows\\System32\\", "") + "\n")
    },
    'settings': {
        'description': translate("settings_command"),
        'function': lambda: settings()
    },
    'virtualization': {
        'description': translate("virtualization_description"),
        'function': lambda: virtualization()
    },
    'logout': {
        'description': translate("logout_command"),
        'function': lambda: logout()
    },
    'powershell': {
        'description': translate("powershell_command"),
        'function': lambda: powershell()
    },
    'newwindow': {
        'description': translate("newwindow_command"),
        'function': lambda: newWindow()
    },
    'ssh': {
        'description': translate("ssh_command"),
        'function': lambda: ssh()
    },
    'monitoring': {
        'description': translate("monitoring_command"),
        'function': lambda: systemInfoMenu()
    },
    'clear': {
        'description': translate("clear_command"),
        'function': lambda: os.system("cls")
    },
    'shutdown': {
        'description': translate("shutdown_command"),
        'function': lambda: os.system("shutdown /s /t 0")
    },
    'restart': {
        'description': translate("restart_command"),
        'function': lambda: os.system("shutdown /r /t 0")
    }
}





def onStart(root_dir):
    try:
        if not os.path.exists(settings_dir):
            os.mkdir(settings_dir)

        if not os.path.exists(root_dir):
            os.mkdir(root_dir)

        settings_file_path = os.path.join(settings_dir, settings_json)

        if not os.path.exists(settings_file_path):
            permissions_grant = {command: "yes" for command in commands}
            data = {
                "loginPage": "yes",
                "users": {
                    "neurasys": "",
                },
                "permissions": {
                    "neurasys": permissions_grant
                }
            }
            safe_write_json(settings_file_path, data)

        version_file_path = os.path.join(settings_dir, version_json)

        if not os.path.exists(version_file_path):
            version_data = {
                "version": "4.0.0-25",
                "checkUpdates": "yes"
            }
            safe_write_json(version_file_path, version_data, temp_name="VersionInfo")

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(f"ONSTART FUNCTION ERROR: {e}")


onStart(currentDirectory)


def loginScreen():
    global currentGroup
    print(translate("welcome"))
    try:
        settings_file_path = os.path.join(settings_dir, settings_json)

        with open(settings_file_path, 'r') as login_set_file:
            data = json.load(login_set_file)

        if data["loginPage"] == "no":
            currentGroup = "default"
            return
        else:
            if "neurasys" in data.get("users", {}):
                print(translate("default_welcome"))
            while True:
                username = input(translate("username"))
                password = input(translate("password"))

                if username in data["users"] and data["users"][username] == password:
                    print(translate("successful_login", username=username))
                    currentGroup = username
                    break
                else:
                    print(translate("invalid_creds"))

    except KeyboardInterrupt:
        os.system("cls")
        loginScreen()

    except Exception as e:
        print(f"LOGINSCREEN FUNCTION ERROR: {e}")


loginScreen()


#COMMAND FUNCTIONS

def help_func():
    try:

        print(translate("ava_commands"))
        for coms in commands:
            print(f"{coms}: {commands[coms]['description']}")

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))

def show_time():
    try:

        time = subprocess.run(["powershell", "-Command", "Get-Date"], capture_output=True, text=True, errors="replace")
        print(time.stdout)

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))

def list_items():
    try:
        files = os.listdir(currentDirectory)
        for item in files:
            item_path = os.path.join(currentDirectory, item)
            if os.path.isdir(item_path):
                print(f"{Fore.GREEN}{item}{Style.RESET_ALL}", end="    ")
            else:
                print(f"{item}", end="    ")

        print("")

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))


prohib_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]


def create():
    try:
        file_name = input(translate("new_file_name_ext_prompt"))

        if file_name == "":
            return print(translate("cannot_be_blank"))
        elif any(char in file_name for char in prohib_chars):
            return print(translate("prohib_chars"))

        file_content = input(translate("file_content_prompt"))

        file_path = os.path.join(currentDirectory, file_name)

        if os.path.exists(file_path):
            choice = input(translate("file_exist_overwrite_prompt", file_name=file_name)).lower()
            if choice == "yes":
                pass
            elif choice == "no":
                return print()
            else:
                return print(translate("invalid_choice"))

        file_content = file_content.replace("\\n", "\n")

        with open(file_path, 'w') as file:
            file.write(file_content)
        print(translate("file_succ_create", file_name=file_name))

    except Exception as e:
        print(translate("error", e=e))



def delete():
    try:
        file_name = input(translate("file_name_ext_prompt"))

        if file_name == "":
            return print(translate("cannot_be_blank"))

        file_path = os.path.join(currentDirectory, file_name)

        if not os.path.exists(file_path):
            return print(translate("file_not_found", file_name=file_name))

        if os.path.isdir(file_path):
            return print(translate("spec_is_dir"))

        os.remove(file_path)
        print(translate("file_del_succ", file_name=file_name))

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))


def read():
    try:
        file_name = input(translate("file_name_ext_prompt"))
        file_path = os.path.join(currentDirectory, file_name)

        if not os.path.exists(file_path):
            return print(translate("file_not_found", file_name=file_name))

        if file_name == "":
            return print(translate("cannot_be_blank"))

        with open(file_path, 'r') as file:
            content = file.read()
        print(content)

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))

def openIMG():
    file_name = input(translate("img_file_prompt"))

    if file_name == "":
        return print(translate("cannot_be_blank"))

    file_path = os.path.join(currentDirectory, file_name)

    if os.path.exists(file_path):
        try:
            subprocess.run(['mspaint.exe', file_path], check=True)

        except KeyboardInterrupt:
            print()

        except Exception as e:
            print(translate("error", e=e))
    else:
        print(translate("file_not_found", file_name=file_name))


def openMP():
    file_name = input(translate("mp_file_prompt"))

    if file_name == "":
        return print(translate("cannot_be_blank"))
    if " " in file_name:
        return print(translate("no_space"))

    source_path = os.path.join(currentDirectory, file_name)
    video_folder = os.path.join(os.path.expanduser("~"), "Videos", file_name)
    destination_path = os.path.join(currentDirectory, file_name)

    if not os.path.exists(source_path):
        return print(translate("file_not_found", file_name=file_name))


    try:

        print(translate("opening"))

        shutil.move(source_path, video_folder)

        process = subprocess.Popen(['start', video_folder], shell=True)

        tm.sleep(1)

        shutil.move(video_folder, destination_path)

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))




def edit():
    file_name = input(translate("file_name_ext_prompt"))

    if file_name == "":
        return print(translate("cannot_be_blank"))

    file_path = os.path.join(currentDirectory, file_name)

    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        print(translate("current_content"))
        for index, line in enumerate(lines):
            print(f"{index + 1}: {line.rstrip()}")

        print(translate("edit_help"))

        new_lines = lines[:]

        while True:
            user_input = input("> ").strip()

            if user_input.lower() == '<save>':
                with open(file_path, 'w') as file:
                    file.writelines(new_lines)
                print(translate("changes_saved"))
                break
            elif user_input.lower() == '<exit>':
                print(translate("changes_discarded"))
                break
            elif user_input.lower() == '<list>':
                print(translate("modif_sofar"))
                for index, line in enumerate(new_lines):
                    print(f"{index + 1}: {line.rstrip()}")
            elif user_input.lower() == '<deletelines>':
                lines_to_delete = input(translate("line_number_to_del_prompt"))
                try:
                    line_numbers = [int(num.strip()) - 1 for num in lines_to_delete.split(',')]
                    line_numbers.sort(reverse=True)
                    for line_number in line_numbers:
                        if 0 <= line_number < len(new_lines):
                            new_lines.pop(line_number)
                            formatted_line_number = line_number + 1

                            print(translate("del_line", formatted_line_number=formatted_line_number))
                        else:
                            formatted_line_number = line_number + 1
                            print(translate("ln_numb_no_exist", formatted_line_number=formatted_line_number))
                except ValueError:
                    print(translate("inv_line_num"))
            else:
                if user_input.startswith('<') and '>' in user_input:
                    try:
                        line_number_str, new_content = user_input[1:].split('>', 1)
                        line_number = int(line_number_str.strip()) - 1
                        if 0 <= line_number < len(new_lines):
                            new_lines[line_number] = new_content.strip() + "\n"
                            formatted_line_number = line_number + 1
                            print(translate("ln_updated", formatted_line_number=formatted_line_number))
                        else:
                            formatted_line_number = line_number + 1
                            print(translate("ln_numb_no_exist", formatted_line_number=formatted_line_number))
                    except (ValueError, IndexError):
                        print(translate("inv_input_format"))
                else:
                    if new_lines and not new_lines[-1].endswith('\n'):
                        new_lines[-1] = new_lines[-1].rstrip() + "\n"
                    new_lines.append(user_input + "\n")
                    print(translate("new_ln", user_input=user_input))
    except KeyboardInterrupt:
        print()

    except FileNotFoundError:
        print(translate("file_not_found", file_name=file_name))
    except Exception as e:
        print(translate("error", e=e))

def rename():
    try:
        old_file_name = input(translate("old_file_name_prompt"))
        new_file_name = input(translate("new_file_name_prompt"))

        old_file_path = os.path.join(currentDirectory, old_file_name)
        new_file_path = os.path.join(currentDirectory, new_file_name)

        if not os.path.exists(old_file_path):
            return print(translate("file_not_found", file_name=old_file_name))

        if old_file_name == "" or new_file_name == "":
            return print(translate("cannot_be_blank"))

        if os.path.isdir(old_file_path):
            return print(translate("folder_no_rename"))

        if any(char in new_file_name for char in prohib_chars):
            return print(translate("prohib_chars"))

        os.rename(old_file_path, new_file_path)
        print(translate("rename_succ", old_file_name=old_file_name, new_file_name=new_file_name))

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))




def run_as_admin(command, cwd):
    try:
        global newWindow
        if newWindow:
            full_command = ["cmd.exe", "/c"] + command
            subprocess.Popen(
                full_command,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        else:
            subprocess.Popen(
                command,
                cwd=cwd,
                shell=True,
            )
    except Exception as e:
        print(f"Error: {e}")


def run():
    global newWindow
    try:
        file_name = input(translate("file_name_ext_prompt")).strip()

        if file_name == "":
            return print(translate("cannot_be_blank"))

        if "--nowindow" in file_name:
            newWindow = False
            file_name = file_name.replace(" --nowindow", "").strip()
        else:
            newWindow = True

        file_path = os.path.join(currentDirectory, file_name)

        if not os.path.exists(file_path):
            return print(translate("file_not_found", file_name=file_name))

        if file_name.endswith(".exe"):
            run_as_admin([file_path], currentDirectory)
        elif file_name.endswith(".msi"):
            run_as_admin(['msiexec', '/i', file_path], currentDirectory)
        elif file_name.endswith(".jar"):
            run_as_admin(['java', '-jar', file_path], currentDirectory)
        elif file_name.endswith(".bat"):
            run_as_admin([file_path], currentDirectory)
        else:
            print(translate("unsup_file_type"))

    except Exception as e:
        print(translate("error", e=e))








def download():
    url = input(translate("enter_url"))

    parsed_url = urlparse(url)
    file_name = os.path.basename(parsed_url.path)
    destination_path = os.path.join(currentDirectory, file_name)



    try:
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))

            with open(destination_path, 'wb') as file:
                with tqdm.tqdm(total=total_size, unit='B', unit_scale=True, desc=file_name) as pbar:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            file.write(chunk)
                            pbar.update(len(chunk))
            formatted_dest = destination_path.replace("C:\\Windows\\System32\\", "")
            print(translate("download_complete", formatted_dest=formatted_dest))
        else:
            print(translate("download_failed"))

    except KeyboardInterrupt:
        print()

    except KeyboardInterrupt:
        print(translate("interrupt_by_user"))
    except Exception as e:
        print(translate("error", e=e))



def copy():
    try:
        file_path = input(translate("copy_source_file_path_prompt"))
        dest_path = input(translate("copy_dest_file_path_prompt"))

        if file_path == "" or dest_path == "":
            return print(translate("paths_blank"))

        if file_path.startswith("root\\"):
            file_path = "C:\\Windows\\System32\\" + file_path

        if dest_path.startswith("root\\"):
            dest_path = "C:\\Windows\\System32\\" + dest_path

        if os.path.isdir(file_path) and os.path.isfile(dest_path):
            return print(translate("copy_into_file"))

        if os.path.isfile(file_path) and os.path.isfile(dest_path):
            return print(translate("copy_file_into_file"))

        if not os.path.exists(dest_path):
            formatted_dest_path = dest_path.replace("C:\\Windows\\System32\\", "")
            return print(translate("folder_not_found", dir_name=formatted_dest_path))

        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                dest_dir_path = os.path.join(dest_path, os.path.basename(file_path))
                if os.path.exists(dest_dir_path):
                    return print(translate("folder_already_exists"))
                print(translate("please_wait"))
                shutil.copytree(file_path, dest_dir_path)
                formatted_file_path = file_path.replace('C:\\Windows\\System32\\', '')
                formatted_dest_path = dest_path.replace('C:\\Windows\\System32\\', '')
                print(translate("copy_succ", formatted_file_path=formatted_file_path, formatted_dest_path=formatted_dest_path))
            elif os.path.isfile(file_path):
                dest_file_path = os.path.join(dest_path, os.path.basename(file_path))
                if os.path.exists(dest_file_path):
                    choice = input(translate("file_exist_overwrite_prompt2")).lower()
                    if choice != "yes":
                        return print(translate("exiting"))
                print(translate("please_wait"))
                shutil.copy2(file_path, dest_file_path)
                formatted_file_path = file_path.replace('C:\\Windows\\System32\\', '')
                formatted_dest_path = dest_file_path.replace('C:\\Windows\\System32\\', '')
                print(translate("copy_succ_file", formatted_file_path=formatted_file_path, formatted_dest_path=formatted_dest_path))
            else:
                raise Exception(translate("not_file_folder"))
        else:
            formatted_file_path = file_path.replace('C:\\Windows\\System32\\', '')
            print(translate("object_not_found", formatted_file_path=formatted_file_path))

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))




def compress():
    files_to_compress = []

    while True:
        user_input = input(translate("comp_file_prompt")).strip()

        if user_input.lower() == 'startcompress':
            if not files_to_compress:
                print(translate("comp_no_added"))
                continue
            break

        if user_input.lower() == "exit":
            return print(translate("exiting"))

        file_path = os.path.join(currentDirectory, user_input)

        if os.path.exists(file_path):
            files_to_compress.append(file_path)
            file_path = file_path.replace("C:\\Windows\\System32\\", "")
            print(translate("added_item", file_path=file_path))
        else:
            print(translate("invalid_path"))

    try:

        zip_file_name = input(translate("outputZIP_name_prompt"))
        zip_file_path = os.path.join(currentDirectory, zip_file_name)

        total_size = 0
        for file in files_to_compress:
            if os.path.isfile(file):
                total_size += os.path.getsize(file)
            elif os.path.isdir(file):
                for dirpath, dirnames, filenames in os.walk(file):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)

        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            with tqdm.tqdm(total=total_size, desc=f"{translate('comp_desc')}", unit="B", unit_scale=True) as progress_bar:
                for file in files_to_compress:
                    if os.path.isdir(file):
                        for dirpath, dirnames, filenames in os.walk(file):
                            for filename in filenames:
                                filepath = os.path.join(dirpath, filename)
                                arcname = os.path.relpath(filepath, start=os.path.dirname(file))
                                zipf.write(filepath, arcname)

                                tm.sleep(0.1)
                                current_zip_size = os.path.getsize(zip_file_path)
                                progress_bar.n = current_zip_size
                                progress_bar.refresh()

                    else:
                        zipf.write(file, os.path.basename(file))
                        tm.sleep(0.1)
                        current_zip_size = os.path.getsize(zip_file_path)
                        progress_bar.n = current_zip_size
                        progress_bar.refresh()

        zip_file_path_formatted = zip_file_path.replace("C:\\Windows\\System32\\", "")
        print(translate("compr_succ", zip_file_path_formatted=zip_file_path_formatted))
    except Exception as e:
        print(translate("error", e=e))




def createDir():
    try:
        dir_name = input(translate("new_folder_name_prompt"))

        if dir_name == "":
            return print(translate("folder_name_blank"))
        elif any(char in dir_name for char in prohib_chars):
            return print(translate("prohib_chars"))

        dir_path = os.path.join(currentDirectory, dir_name)

        if not os.path.exists(os.path.join(currentDirectory, dir_name)):
            os.makedirs(dir_path)
            print(translate("folder_created_succ", dir_name=dir_name))
        else:
            print(translate("fl_alr_exist", dir_name=dir_name))

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))


def deleteDir():
    try:
        dir_name = input(translate("name_folder_prompt"))

        dir_path = os.path.join(currentDirectory, dir_name)

        if dir_name == "":
            return print(translate("folder_name_blank"))

        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(translate("fl_del_succ", dir_name=dir_name))
        else:
            return print(translate("folder_not_found", dir_name=dir_name))

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))



def changeDir():
    global currentDirectory
    try:
        new_dir = input(translate("cd_folder_nm_prompt"))

        if new_dir.startswith("C:\\"):
            return print(translate("unable_to_cd_C"))

        if os.path.isfile(new_dir):
            return print(translate("cannot_change_file"))

        new_dir_path = os.path.join(currentDirectory, new_dir)

        if not os.path.exists(new_dir_path):
            return print(translate("folder_not_found", dir_name=new_dir))


        currentDirectory = os.path.join(currentDirectory, new_dir)
        formatted_cd = currentDirectory.replace("C:\\Windows\\System32\\", "")
        print(translate("succ_change", formatted_cd=formatted_cd))

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))



def backDir():
    global currentDirectory
    try:
        parentDir = f"{os.path.dirname(currentDirectory)}\\"
        if currentDirectory == "C:\\Windows\\System32\\root\\":
            print(translate("alr_root"))
        else:
            if currentDirectory != "C:\\":
                currentDirectory = "C:\\Windows\\System32\\root\\"
                formatted_cd = currentDirectory.replace("C:\\Windows\\System32\\", "")
                print(translate("succ_backdir", formatted_cd=formatted_cd))
                return
            currentDirectory = parentDir
            formatted_cd = currentDirectory.replace("C:\\Windows\\System32\\", "")
            print(translate("succ_backdir", formatted_cd=formatted_cd))

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))




def settings():
    print(translate("settings_options"))

    choice = input(translate("choose_action_exit_prompt")).lower()
    if choice == "exit":
        return print(translate("exiting"))

    if choice == "1":
        userAuth()
    elif choice == "2":
        networkSettings()
    elif choice == "3":
        print(translate("drives_options"))

        action = input(translate("choose_action_exit_prompt")).lower()
        if action == "exit":
            return print(translate("exiting"))

        if action == "1":
            list_drive_info()
        elif action == "2":
            mount_iso()
        elif action == "3":
            eject_drive()
        else:
            print(translate("invalid_choice"))


    elif choice == "4":
        try:
            timeout = input(translate("monitor_timeout_prompt")).lower()

            if timeout == "exit":
                return print(translate("exiting"))
            elif timeout < "0":
                raise ValueError

            subprocess.run(['powercfg', '/change', 'monitor-timeout-ac', timeout], check=True)
            subprocess.run(['powercfg', '/change', 'monitor-timeout-dc', timeout], check=True)

            print(translate("monitor_timeout_set", timeout=timeout))

        except KeyboardInterrupt:
            print()

        except ValueError:
            print(translate("inv_number"))
        except Exception as e:
            print(translate("error", e=e))

    elif choice == "5":
        try:
            timeout = input(translate("comp_timeout_prompt"))

            if timeout == "exit":
                return print(translate("exiting"))
            elif timeout < "0":
                raise ValueError

            subprocess.run(['powercfg', '/change', 'standby-timeout-ac', timeout], check=True)
            subprocess.run(['powercfg', '/change', 'standby-timeout-dc', timeout], check=True)

            print(translate("comp_timeout_set", timeout=timeout))

        except KeyboardInterrupt:
            print()

        except ValueError:
            print(translate("inv_number"))
        except Exception as e:
            print(translate("error", e=e))
    elif choice == "6":
        uninstall()
    elif choice == "7":
        change_computer_name()
    elif choice == "8":
        set_volume()
    elif choice == "9":
        global current_language
        for language in ava_lang_short:
            print(language, end="    ")

        while True:
            new_lang = input(translate("choose_lang_prompt")).capitalize()
            if new_lang == "Exit":
                break

            elif new_lang not in ava_lang_short:
                print(translate("inv_lang"))
            else:
                current_language = ava_lang_short[new_lang]
                with open(translations_json_path, 'r', encoding='utf-8', errors='replace') as fl:
                    data = json.load(fl)

                data["language"] = ava_lang_short[new_lang]

                with open(translations_json_path, 'w', encoding='utf-8', errors='replace') as file:
                    json.dump(data, file)

                print(translate("lang_set_succ", new_lang=new_lang))
                break

    elif choice == "10":
        try:
            with open(os.path.join(settings_dir, version_json), 'r') as file:
                data = json.load(file)
            while True:
                choice = input(translate("update_check_prompt")).lower()

                if choice == "enable":
                    data["checkUpdates"] = "true"
                    print(translate("update_check_ena"))
                    break
                elif choice == "disable":
                    data["checkUpdates"] = "false"
                    print(translate("update_check_dis"))
                    break
                elif choice == "exit":
                    print(translate("exiting"))
                    break
                else:
                    print(translate("invalid_choice"))



            safe_write_json(os.path.join(settings_dir, version_json), data, 'version')


        except KeyboardInterrupt:
            print()

        except Exception as e:
            print(translate("error", e=e))

    elif choice == "11":
        try:
            subprocess.run(["cmd", "/c", "start" ,"taskschd.msc"])

        except KeyboardInterrupt:
            print()

        except Exception as e:
            print(translate("error", e=e))
    else:
        return print(translate("invalid_action"))


def checkUpdates():
    try:
        if not os.path.exists(os.path.join(settings_dir, version_json)):
            data = {"version": "4.0.0-25"}
            safe_write_json(os.path.join(settings_dir, version_json), data, "CheckUpdates")


        with open(os.path.join(settings_dir, version_json), 'r') as file:
            data = json.load(file)

        if data["checkUpdates"] == "false":
            return

        current_version = data["version"]

        latest_version_url = 'https://raw.githubusercontent.com/Cl9s4bl3/neurasys-web/main/latest_version.json'


        response = requests.get(latest_version_url)
        response.raise_for_status()

        latest_info = response.json()
        latest_version = latest_info.get("version")

        if latest_version == "":
            return print(translate("error"))

        if latest_version == current_version:
            return
        else:
            return print(translate("new_upd_ava", latest_version=latest_version))


    except requests.RequestException as e:
        return

    except json.JSONDecodeError as f:
        return
    except ValueError as g:
        return

    except Exception as h:
        print(translate("error", e=h))



checkUpdates()

restart_required = False
def virtualization():
    global restart_required
    try:

        present = subprocess.run(["powershell", "-Command", "Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All"], text=True, capture_output=True, shell=True)

        if restart_required:
            return print("A system restart is required to run Hyper-V.")

        if "State            : Enabled" in present.stdout:
            subprocess.run(["powershell", "-Command", "virtmgmt.msc"])
        else:
            choice = input("Hyper-V is not installed on the system. Would you like to install it (yes/no)? ")

            if choice == "yes":
                install_command = "Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All -NoRestart"
                subprocess.run(["powershell", "-Command", install_command], text=True, capture_output=True, shell=True)
                print("Hyper-V is now installed. Restart your computer to apply the changes.")
                restart_required = True
                return
            elif choice == "no":
                print("Exiting...")
                return

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(f"An error occurred: {str(e)}")





def userAuth():
    print(translate("user_options"))

    choice = input(translate("choose_action_exit_prompt")).lower()

    if choice == "exit":
        return print(translate("exiting"))

    if choice == "1":
        try:

            with open(os.path.join(settings_dir, settings_json), 'r') as file:
                data = json.load(file)

            action = input(translate("login_page_prompt")).lower()

            if action == "enable":
                data["loginPage"] = "yes"
                print(translate("ena_login_page"))
            elif action == "disable":
                data["loginPage"] = "no"
                print(translate("dis_login_page"))
            else:
                return print(translate("invalid_choice"))

            with open(os.path.join(settings_dir, settings_json), 'w') as file:
                json.dump(data, file)

        except KeyboardInterrupt:
            print()

        except Exception as e:
            print(translate("error", e=e))
    elif choice == "2":
        global currentGroup
        try:

            username = input(translate("new_group_username_prompt"))

            if username == "":
                print(translate("username_blank"))
                return

            password = input(translate("new_group_password_prompt"))

            with open(os.path.join(settings_dir, settings_json), 'r') as file:
                data = json.load(file)

            if "users" not in data:
                data["users"] = {}
            if "permissions" not in data:
                data["permissions"] = {}

            if username in data["users"]:
                print(translate("group_alr_exist", username=username))
                return

            data["users"][username] = password
            data["permissions"][username] = {}

            always_ena_coms = ["help", "logout"]

            for command in commands:
                if command in always_ena_coms:
                    data["permissions"][username][command] = "yes"
                    print(translate("command_always_ena", command=command))
                else:
                    while True:
                        choice = input(translate("ena_command_group_prompt", command=command, username=username)).strip().lower()
                        if choice in {"yes", "no"}:
                            data["permissions"][username][command] = "yes" if choice == "yes" else "no"
                            break
                        else:
                            print(translate("inv_group_input"))

            if "neurasys" in data["users"]:
                del data["users"]["neurasys"]
                if not data["permissions"][username]["settings"] == "yes":
                    return print(translate("not_admin_user"))
                else:
                    currentGroup = username

            if "neurasys" in data["permissions"]:
                del data["permissions"]["neurasys"]
                if not data["permissions"][username]["settings"] == "yes":
                    return print(translate("not_admin_user"))
                else:
                    currentGroup = username

            with open(os.path.join(settings_dir, settings_json), 'w') as file:
                json.dump(data, file)

            print(translate("group_succ_added", username=username))

        except KeyboardInterrupt:
            print()

        except Exception as e:
            print(translate("error", e=e))

    elif choice == "3":
        try:
            username = input(translate("remove_group_username_promopt"))

            if username == "":
                print(translate("username_blank"))
                return

            if username == currentGroup:
                return print(translate("in_remove_group"))

            with open(os.path.join(settings_dir, settings_json), 'r') as file:
                data = json.load(file)

            if username == "neurasys":
                other_users = [user for user in data["users"] if user != "neurasys"]
                if not other_users:
                    print(translate("cant_delete_neurasys"))
                    return

            password = input(translate("remove_group_password_prompt"))



            if username not in data.get("users", {}):
                print(translate("group_not_exist", username=username))
                return

            if data["users"][username] != password:
                print(translate("incorrect_pass"))
                return

            del data["users"][username]

            if username in data.get("permissions", {}):
                del data["permissions"][username]

            with open(os.path.join(settings_dir, settings_json), 'w') as file:
                json.dump(data, file)

            print(translate("remove_succ_group", username=username))

        except KeyboardInterrupt:
            print()

        except Exception as e:
            print(translate("error", e=e))
    else:
        return print(translate("invalid_choice"))


def logout():

    if currentGroup == "default":
        return print(translate("unable_logout"))

    os.system("cls")
    loginScreen()

def powershell():
    subprocess.run(["powershell"])

def newWindow():
    try:
        subprocess.Popen(["cmd", "/c", "C:\\Windows\\System32\\neurasys.exe"], creationflags=CREATE_NEW_CONSOLE)

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))


current_version_data = ""

def load_version():
    global current_version_data
    with open(os.path.join(settings_dir, version_json), 'r') as ver_file:
        current_version_data = json.load(ver_file)

load_version()

def updateMenu():
    print(translate("update_menu_options"))


    choice = input(translate("choose_action_exit_prompt")).lower()

    if choice == "exit":
        return print(translate("exiting"))
    elif choice == "1":
        update()
    elif choice == "2":
        print(translate("current_version"), current_version_data["version"])
    else:
        print(translate("invalid_choice"))


def update():
    iso_name = input(translate("iso_name_prompt"))
    iso_file = os.path.join(currentDirectory, iso_name)

    print(translate("beta_feature_warning"))
    decision = input(translate("warning_continue_prompt")).lower()
    if decision == "yes":
        pass
    else:
        return print(translate("exiting"))

    print(translate("overwrite_warning"))
    choice = input(translate("warning_continue_prompt"))
    if choice == "yes":
        pass
    else:
        return print(translate("exiting"))

    if not os.path.exists(iso_file):
        print(translate("iso_file_not_found"))
        return
    print(translate("prep_install"))

    os.remove(os.path.join(settings_dir, version_json))
    os.remove(os.path.join(settings_dir, settings_json))

    eject_all = '$cdDrive = (Get-WmiObject -Query "SELECT * FROM Win32_LogicalDisk WHERE DriveType = 5").DeviceID; (New-Object -ComObject Shell.Application).Namespace(17).ParseName($cdDrive).InvokeVerb("Eject")'

    subprocess.run(["powershell", "-Command", eject_all], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tm.sleep(3)
    print(translate("prep_install_files"))
    mount_command = f"PowerShell Mount-DiskImage -ImagePath '{iso_file}'"
    result = subprocess.run(mount_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        print(translate("iso_file_not_found"))
        tm.sleep(5)
        os.system("shutdown /r /t 0")
        return

    tm.sleep(3)

    iso_drive = None
    for letter in range(ord('D'), ord('Z') + 1):
        drive = chr(letter) + ":"
        if os.path.exists(drive + "\\"):
            try:
                volume_info = subprocess.check_output(
                    f'PowerShell "Get-Volume -DriveLetter {drive[0]}"',
                    shell=True,
                    stderr=subprocess.DEVNULL
                ).decode()
                if "CD-ROM" in volume_info:
                    iso_drive = drive
                    break

            except KeyboardInterrupt:
                print()

            except subprocess.CalledProcessError:
                continue

    if not iso_drive:
        print(translate("iso_file_not_found"))
        tm.sleep(5)
        os.system("shutdown /r /t 0")
        return

    source_main_exe = f"{iso_drive}/core/neurasys.exe"
    if not os.path.exists(source_main_exe):
        print(translate("neurasys_exe_not_found", source_main_exe=source_main_exe))
        tm.sleep(5)
        os.system("shutdown /r /t 0")
        return
    username = os.getlogin()

    batch_content = f"""@echo off
    taskkill /f /im neurasys.exe > nul 2>&1
    echo Please wait...
    timeout /t 5 /nobreak > NUL
    echo Copying files...
    xcopy /Y /F "{source_main_exe}" "C:/Windows/System32/neurasys.exe" > nul 2>&1
    if errorlevel 1 (
        echo Failed to copy neurasys.exe. Check if it is in use or if you have permission.
    ) else (
        echo {translate("files_copied_succ")}
    )

    :: Eject the ISO
    echo Cleaning up...
    PowerShell Dismount-DiskImage -ImagePath '{iso_file}' > $null 2>&1

    :: Delete this batch file
    timeout /t 3 /nobreak > NUL
    shutdown /r /t 0
    del replace_main.bat > NUL 2>&1

    """
    with open("replace_main.bat", "w") as batch_file:
        batch_file.write(batch_content)

    subprocess.run("replace_main.bat", shell=True)



def bytes_to_gb(bytes):
    return bytes / (1024 ** 3)


def list_drive_info():
    drives = psutil.disk_partitions()
    drive_info = []


    for drive in drives:
        try:
            drive_usage = psutil.disk_usage(drive.mountpoint)
            drive_info.append({
                "drive": drive.device,
                "mountpoint": drive.mountpoint,
                "total_size": bytes_to_gb(drive_usage.total),
                "used": bytes_to_gb(drive_usage.used),
                "free": bytes_to_gb(drive_usage.free),
                "opts": drive.opts
            })

        except KeyboardInterrupt:
            print()

        except PermissionError:
            perm_error_device = drive.device
            print(translate("perm_error_drive", perm_error_device=perm_error_device))


    for drive in drive_info:
        print(translate("drive"),  drive['drive'])
        print(translate("total_size"), f"{drive['total_size']:.2f} GB")
        print(translate("used_space"), f"{drive['used']:.2f} GB")
        print(translate("free_space"), f"{drive['free']:.2f} GB")
        print(translate("options"), f"{drive['opts']}")
        print()


def mount_iso():
    file_name = input(translate("iso_name_prompt"))
    iso_path = os.path.join("C:\\Windows\\System32\\", currentDirectory, file_name)
    try:
        command = f'Mount-DiskImage -ImagePath "{iso_path}"'
        subprocess.run(["powershell", "-Command", command], check=True)
        print(translate("mount_succ", file_name=file_name))

    except KeyboardInterrupt:
        print()

    except subprocess.CalledProcessError as e:
        print(translate("error", e=e))


def eject_drive():
    drive_letter = input(translate("drv_letter_prompt")).upper()

    if drive_letter.endswith(":\\"):
        pass
    else:
        drive_letter = drive_letter.upper().rstrip(':') + ':\\'

    drive_type = win32file.GetDriveType(drive_letter)

    DRIVE_REMOVABLE = 2
    DRIVE_CDROM = 5

    if drive_type not in [DRIVE_REMOVABLE, DRIVE_CDROM]:
        print(translate("not_usb_nor_cd", drive_letter=drive_letter))
        return

    drive_handle = win32file.CreateFile(
        f"\\\\.\\{drive_letter[0]}:",
        win32file.GENERIC_READ,
        win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
        None,
        win32file.OPEN_EXISTING,
        0,
        None
    )

    IOCTL_STORAGE_EJECT_MEDIA = 0x2D4808

    result = ctypes.c_ulong()

    eject_status = ctypes.windll.kernel32.DeviceIoControl(
        drive_handle.handle,
        IOCTL_STORAGE_EJECT_MEDIA,
        None,
        0,
        None,
        0,
        ctypes.byref(result),
        None
    )

    win32file.CloseHandle(drive_handle)

    if eject_status:
        print(translate("eject_succ", drive_letter=drive_letter))
    else:
        print(translate("error", e=e))


def uninstall():
    print(translate("loading_progs"))
    powershell_cmd = 'Get-WmiObject -Class Win32_Product | Select-Object -Property Name'
    result = subprocess.run(["powershell", "-Command", powershell_cmd], capture_output=True, text=True)

    programs = result.stdout.strip().split('\n')[3:]
    programs = [program.strip() for program in programs if program.strip()]

    if not programs:
        print(translate("no_progs"))
        return

    while True:
        print(translate("ins_progs"))
        for idx, program in enumerate(programs, 1):
            print(f"{idx}. {program}")

        choice = input(translate("program_number_prompt"))

        if choice.lower() == 'q':
            print(translate("exiting"))
            break

        try:
            choice = int(choice)
            if 1 <= choice <= len(programs):
                program_name = programs[choice - 1]
                print(translate("unsins_progg", program_name=program_name))

                uninstall_cmd = f'Get-WmiObject -Class Win32_Product | Where-Object {{ $_.Name -eq "{program_name}" }} | ForEach-Object {{ $_.Uninstall() }}'
                subprocess.run(["powershell", "-Command", uninstall_cmd], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                print(translate("unins_succ"))
                break
            else:
                print(translate("invalid_choice"))

        except KeyboardInterrupt:
            print()

        except ValueError:
            print(translate("inv_number"))
        except Exception as e:
            print(translate("error", e=e))


def ssh():
    print(translate("ssh_options"))

    choice = input(translate("choose_action_exit_prompt"))

    if choice == "1":
        installSSH()
    elif choice == "2":
        uninstallSSH()
    elif choice == "exit":
        return print(translate("exiting"))
    else:
        return print(translate("exiting"))


def uninstallSSH():
    try:

        exist = subprocess.run(
            ["powershell", "-Command",
             "Get-WindowsCapability -Online | Where-Object {$_.Name -like 'OpenSSH.Server*'}"],
            capture_output=True, text=True
        )

        if "NotPresent" in exist.stdout:
            return print(translate("ssh_not_installed"))
        else:
            subprocess.run(["powershell", "-Command", "Remove-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0"])
            print(translate("ssh_unins_succ"))

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))

def check_internet(timeout=5):
    url = "http://www.google.com"
    try:
        response = requests.head(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

def installSSH():
    username = "NeuraSys"
    ssh_config_setting = "ForceCommand"
    ssh_config_value = r"C:\Windows\System32\neurasys.exe"

    if check_internet():
        pass
    else:
        return print(translate("no_internet_conn"))

    try:
        installed = subprocess.run(
            ["powershell", "-Command",
             "Get-WindowsCapability -Online | Where-Object {$_.Name -like 'OpenSSH.Server*'}"],
            capture_output=True, text=True
        )

        if installed.returncode != 0:
            print(translate("error", e=None))
            return

        if "Installed" not in installed.stdout:
            print(translate("ins_in_prog"))
            subprocess.run(["powershell", "-Command", "Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0"])
            print(translate("ins_prog"))
        else:
            print(translate("ssh_alr_ins"))

        subprocess.run(["powershell", "-Command", "Start-Service sshd"])
        subprocess.run(["powershell", "-Command", "Set-Service -Name sshd -StartupType 'Automatic'"])


        while True:
            new_password = input(translate("ssh_pass_prompt"))
            if not new_password == "":
                break
            else:
                print(translate("pass_blank"))
        subprocess.run(["net", "user", username, new_password], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(translate("ssh_pass_succ"))

        sshd_config_path = r"C:\ProgramData\ssh\sshd_config"

        found_force_command = False

        with open(sshd_config_path, 'r') as file:
            lines = file.readlines()

        with open(sshd_config_path, 'w') as file:
            for line in lines:

                if line.strip().startswith(ssh_config_setting):
                    found_force_command = True
                    file.write(line)

                else:
                    file.write(line)

            if not found_force_command:
                if not found_force_command:
                    file.write(f"{ssh_config_setting} {ssh_config_value}\n")

        subprocess.run(["powershell", "-Command", "Restart-Service sshd"])

        subprocess.run(
            ["powershell", "-Command",
             "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon' -Name 'AutoAdminLogon' -Value '1'"],
            check=True
        )
        subprocess.run(
            ["powershell", "-Command",
             f"Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon' -Name 'DefaultUserName' -Value '{username}'"],
            check=True
        )
        subprocess.run(
            ["powershell", "-Command",
             f"Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon' -Name 'DefaultPassword' -Value '{new_password}'"],
            check=True
        )
        print(translate("ssh_ins_succ"))

    except KeyboardInterrupt:
        print()

    except subprocess.CalledProcessError as e:
        print(translate("error", e=e))
    except Exception as e:
        print(translate("error", e=e))




def get_current_computer_name():
    return os.getenv('COMPUTERNAME')

def change_computer_name():

    new_name = input(translate("comp_name_prompt"))

    if new_name == "exit":
        return print(translate("exiting"))

    if len(new_name) > 15:
        print(translate("longer_than15"))
        return
    prohib_hostname_chars = ["*", "/", "\\", "?", ":", "|", '"', "<", ">", " "]
    if any(char in new_name for char in prohib_hostname_chars):
        print(translate("prohib_chars"))
        return

    try:
        subprocess.run(
            ["powershell", "-Command", f'Rename-Computer -NewName "{new_name}"'],
            check=True,
            shell=True,
            stdout=subprocess.DEVNULL,
        )
        print(translate("hostname_succ", new_name=new_name))

    except KeyboardInterrupt:
        print()

    except subprocess.CalledProcessError as e:
        print(translate("error", e=e))

def set_volume():
    try:

        volume_level = float(input(translate("volume_per_prompt")))
        if volume_level < 0 or volume_level > 100:
            return print(translate("inv_number"))

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))


        volume.SetMasterVolumeLevelScalar(volume_level / 100.0, None)

        current_volume = volume.GetMasterVolumeLevelScalar() * 100
        current_volume_formatted = f"{current_volume:.0f}"
        print(translate("volume_succ", current_volume_formatted=current_volume_formatted))

    except KeyboardInterrupt:
        print()

    except ValueError:
        print(translate("inv_number"))
    except Exception as e:
        print(translate("volume_not_supported"))




def systemInfoMenu():
    print(translate("sys_info_options"))

    option = input(translate("choose_action_exit_prompt")).lower()
    if option == "exit":
        return print(translate("exiting"))

    if option == "1":
        sysInfo()
    elif option == "2":
        show_system_usage()
    elif option == "3":

        try:
            battery = psutil.sensors_battery()

            if battery:
                battery_perc = battery.percent
                battery_plugged = battery.power_plugged

                print(translate("battery_status", battery_perc=battery_perc, battery_plugged=battery_plugged))

            else:
                return print(translate("inf_not_ava"))

        except KeyboardInterrupt:
            print()

        except Exception as e:
            print(translate("error", e=e))

    else:
        return print(translate("exiting"))

def show_system_usage():
    print(translate("getting_info"))
    try:

        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        print(translate("cpu_usage"), f"{cpu_usage}%")
        memory_perc = memory_info.percent
        memory_used = f"{memory_info.used / (1024 ** 3):.2f}"
        memory_total = f"{memory_info.total / (1024 ** 3):.2f}"
        print(translate("memory_usage", memory_perc=memory_perc, memory_used=memory_used, memory_total=memory_total))

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))



def sysInfo():
    print(translate("getting_info"))
    try:
        commands = {
            "hostname": "(Get-WmiObject Win32_ComputerSystem).Name",
            "machine": "[Environment]::Is64BitOperatingSystem",
            "processor": "(Get-WmiObject Win32_Processor).Name",
            "cpu_count": "(Get-WmiObject Win32_ComputerSystem).NumberOfLogicalProcessors",
            "cpu_freq": "(Get-WmiObject Win32_Processor).MaxClockSpeed",
            "total_memory": "(Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory",
            "available_memory": "(Get-WmiObject Win32_OperatingSystem).FreePhysicalMemory"
        }

        results = {}
        for key, command in commands.items():
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True
            )
            results[key] = result.stdout.strip()

        total_memory = int(results["total_memory"])
        available_memory_kb = int(results["available_memory"]) * 1024
        used_memory = total_memory - available_memory_kb

        results["total_memory_gb"] = total_memory / (1024 ** 3)
        results["available_memory_gb"] = available_memory_kb / (1024 ** 3)
        results["used_memory_gb"] = used_memory / (1024 ** 3)

        hostname_data = results['hostname']
        version_data = current_version_data["version"]
        architecture_data = '64-bit' if results['machine'] == 'True' else '32-bit'
        processor_data = results['processor']
        core_count_data = results['cpu_count']
        cpu_freq_data = results['cpu_freq']
        total_memory_data = f"{results['total_memory_gb']:.2f}"
        available_memory_data = f"{results['available_memory_gb']:.2f}"
        used_memory_data = f"{results['used_memory_gb']:.2f}"

        print(translate("sys_info", hostname_data=hostname_data, version_data=version_data, architecture_data=architecture_data, processor_data=processor_data, core_count_data=core_count_data, cpu_freq_data=cpu_freq_data, total_memory_data=total_memory_data, used_memory_data=used_memory_data, available_memory_data=available_memory_data))

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))





def networkSettings():
    print(translate("network_settings_options"))

    choice = input(translate("choose_action_exit_prompt")).lower()

    if choice == "exit":
        return print(translate("exiting"))
    elif choice == "1":
        enable_wifi()
    elif choice == "2":
        get_ipconfig()
    elif choice == "3":
        changeIPPrint()
    elif choice == "4":
        change_dns()
    elif choice == "5":
        reset_ip()
    elif choice == "6":
        firewall()
    elif choice == "7":
        ping_host()
    else:
        return print(translate("invalid_choice"))


def enable_wifi():
    subprocess.run(
        'netsh interface set interface name="Wi-Fi" admin=enabled',
        shell=True,
        capture_output=True,
        text=True
    )

    result = subprocess.run(
        'netsh wlan show networks',
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(translate("unsupported_wifi"))
        return
    else:
        print(result.stdout)

    choice = input(translate("connect_disconnect_prompt")).lower()
    if choice == "connect":
        pass
    elif choice == "disconnect":
        os.system('cmd /c "netsh wlan disconnect > NUL 2>&1"')
        print(translate("disconnect_succ"))
        return
    else:
        return print(translate("invalid_choice"))



    wifi_name = input(translate("SSID_prompt"))

    if wifi_name == "":
        return print(translate("invalid_ssid"))

    wifi_password = input(translate("network_password_prompt"))

    profile_content = f"""
    <WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
        <name>{wifi_name}</name>
        <SSIDConfig>
            <SSID>
                <name>{wifi_name}</name>
            </SSID>
        </SSIDConfig>
        <connectionType>ESS</connectionType>
        <connectionMode>auto</connectionMode>
        <MSM>
            <security>
                <authEncryption>
                    <authentication>WPA2PSK</authentication>
                    <encryption>AES</encryption>
                    <useOneX>false</useOneX>
                </authEncryption>
                <sharedKey>
                    <keyType>passPhrase</keyType>
                    <protected>false</protected>
                    <keyMaterial>{wifi_password}</keyMaterial>
                </sharedKey>
            </security>
        </MSM>
    </WLANProfile>
    """

    profile_path = f"{wifi_name}.xml"
    with open(profile_path, 'w') as file:
        file.write(profile_content)

    os.system(f'cmd /c "netsh wlan add profile filename={profile_path} > NUL 2>&1"')

    os.system(f'cmd /c "netsh wlan connect name={wifi_name} > NUL 2>&1"')

    print(translate("connection_request"))


def get_ipconfig():
    result = subprocess.run(['ipconfig','/all'], capture_output=True, text=True, encoding='utf-8', errors='replace')

    output = result.stdout
    print(output)

def get_friendly_interface_names():
    try:
        result = subprocess.run(['netsh', 'interface', 'show', 'interface'], capture_output=True, text=True, check=True)
        output = f"\n{result.stdout}"

        interfaces = {}
        lines = output.splitlines()
        for line in lines:
            if any(keyword in line for keyword in ['Dedicated', 'Loopback', 'Wi-Fi', 'Ethernet']):
                parts = line.split()
                if len(parts) >= 4:
                    name = ' '.join(parts[3:])
                    interfaces[name.lower()] = name
        return interfaces

    except KeyboardInterrupt:
        print()

    except subprocess.CalledProcessError as e:
        print(translate("error", e=e))
        return {}

def change_ip(interface_name, new_ip, new_subnet, new_gateway=None):
    try:
        if new_gateway:
            ip_command = [
                'netsh', 'interface', 'ipv4', 'set', 'address',
                f'name={interface_name}', 'static', new_ip, new_subnet, new_gateway
            ]
        else:
            ip_command = [
                'netsh', 'interface', 'ipv4', 'set', 'address',
                f'name={interface_name}', 'static', new_ip, new_subnet
            ]

        result = subprocess.run(ip_command, capture_output=True, text=True)

        if result.returncode == 0:
            print(translate("ip_change_succ", new_ip=new_ip, new_subnet=new_subnet, interface_name=interface_name))
            if new_gateway:
                print(translate("gateway_succ", new_gateway=new_gateway, interface_name=interface_name))
        else:
            print(translate("error", e=result.stderr))

    except KeyboardInterrupt:
        print()

    except subprocess.CalledProcessError as e:
        print(translate("error", e=e))

def changeIPPrint():
    interfaces = get_friendly_interface_names()
    if not interfaces:
        print(translate("no_interfaces"))
        return

    print(translate("ava_interfaces"))
    for index, name in interfaces.items():
        print(f"{index}: {name}")

    interface_name = input(translate("interface_name_prompt")).lower()
    if interface_name not in interfaces:
        print(translate("invalid_interfaces"))
        return

    new_ip = input(translate("new_ip_prompt"))
    new_subnet = input(translate("subnetmask_prompt"))
    new_gateway = input(translate("default_gateway_prompt"))
    new_gateway = new_gateway if new_gateway else None

    change_ip(interfaces[interface_name], new_ip, new_subnet, new_gateway)

def change_dns():
    interfaces = get_friendly_interface_names()
    if not interfaces:
        print(translate("no_interfaces"))
        return

    print(translate("ava_interfaces"))
    for index, name in interfaces.items():
        print(f"{index}: {name}")

    interface_name = input(translate("interface_name_prompt")).lower()
    if interface_name not in interfaces:
        print(translate("invalid_interfaces"))
        return

    new_dns = input(translate("new_dns_prompt"))

    try:
        dns_command = ['netsh', 'interface', 'ipv4', 'set', 'dns', f'name={interfaces[interface_name]}', 'static', new_dns]
        result = subprocess.run(dns_command, capture_output=True, text=True)

        if result.returncode == 0:
            formatted_interface_name = interfaces[interface_name]
            print(translate("dns_succ", new_dns=new_dns, formatted_interface_name=formatted_interface_name))
        else:
            print(translate("error", e=result.stderr))

    except KeyboardInterrupt:
        print()

    except subprocess.CalledProcessError as e:
        print(translate("error", e=e))

def reset_ip():
    interfaces = get_friendly_interface_names()
    if not interfaces:
        print(translate("no_interfaces"))
        return

    print(translate("ava_interfaces"))
    for index, name in interfaces.items():
        print(f"{index}: {name}")

    interface_name = input(translate("interface_name_prompt")).lower()
    if interface_name not in interfaces:
        print(translate("invalid_interfaces"))
        return

    try:
        reset_command = ['netsh', 'interface', 'ipv4', 'set', 'address', f'name={interfaces[interface_name]}', 'source=dhcp']
        result = subprocess.run(reset_command, capture_output=True, text=True)

        if result.returncode == 0:
            formatted_interface_name = interfaces[interface_name]
            print(translate("dhcp_succ", formatted_interface_name=formatted_interface_name))
        else:
            print(translate("error", e=result.stderr))

    except KeyboardInterrupt:
        print()

    except subprocess.CalledProcessError as e:
        print(translate("error", e=e))


def ping_host():
    host = input(translate("ping_prompt"))
    subprocess.run(["ping", host])

def firewall():
    try:
        os.system("wf.msc")

    except KeyboardInterrupt:
        print()

    except Exception as e:
        print(translate("error", e=e))



def completer(text, state):
    options = [cmd for cmd in commands if cmd.startswith(text)]
    if state < len(options):
        return options[state]
    return None

readline.set_completer(completer)
readline.parse_and_bind("tab: complete")

while True:
    formatted_current_group = ""
    set_console_title("NeuraSys")
    if currentGroup == "default":
        formatted_current_group = "root"
    else:
        formatted_current_group = currentGroup

    try:
        with open(os.path.join(settings_dir, settings_json), "r") as f:
            settings_file = json.load(f)

        command_input = input(f"\n{formatted_current_group}@{hostname}>").lower()

        if command_input not in commands:
            print(translate("invalid_command", command_input=command_input))
            continue

        permissions = settings_file["permissions"].get(currentGroup, {})

        if currentGroup == "default" or settings_file["permissions"].get(currentGroup, {}).get(command_input) == "yes":
            command_func = commands[command_input]["function"]
            command_func()
        else:
            print(translate("perm_denied", command_input=command_input))

    except KeyboardInterrupt:
        print()
    except Exception as e:
        print(f"COMMAND_INPUT_ERROR: {e}")