#! /usr/bin/env python3

import gi
import os
import requests
import json
import re
import uuid
import hashlib
import time
import sys
import platform
import gettext
import datetime

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk

gettext.bindtextdomain('uncom-activate', '/usr/share/uncom/uncom-license/locale')
gettext.textdomain('uncom-license')
_ = gettext.gettext

# Configuration of application
PATH_TO_KEY_FILE = "/usr/local/uncom-setup/files/.uncom_license"
PATH_TO_TRIAL_FILE = "/usr/local/uncom-setup/files/.uncom_trial"
PATH_TO_UUID = "/usr/share/upmd/data"
LICENSE_SERVER_URL = "https://activate.uncom.tech/"
SUPPORT_URL = "https://t.me/UncomOS/"
PURCHASE_URL = "https://uncom.tech/buy/"
ICON_NAME = "org.uncom.activator"
EXIT_CODE = 1

class RequestKeyWindow(Gtk.Window):
        def __init__(self):
                super().__init__(title=_("Активация Uncom OS")) # Активация Uncom OS
                self.set_border_width(10)
                self.set_default_size(500, 150)
                self.set_resizable(False)
                self.set_position(Gtk.WindowPosition.CENTER)

                # Main window container
                self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                self.add(self.vbox)

                icon_pixbuf_list = get_icon_pixbuf_list(ICON_NAME)
                if len(icon_pixbuf_list)!=0:
                        self.set_default_icon_list(icon_pixbuf_list)
                        #icon = Gtk.Image.new_from_pixbuf(icon_pixbuf_list[-1:][0])
                        #self.vbox.pack_start(icon, False, False, 0)

                # Messages
                label_message = Gtk.Label()
                label_message.set_text(_("Добро пожаловать в Uncom OS.\nПожалуйста, активируйте вашу копию операционной системы.")) # Добро пожаловать в Uncom OS.\nПожалуйста, активируйте вашу копию операционной системы.
                label_message.set_halign(Gtk.Align.START)
                label_message.set_line_wrap(True)
                self.vbox.pack_start(label_message, True, True, 0)

                # Activation key label
                self.label_prompt = Gtk.Label()
                self.label_prompt.set_text(_("Ключ активации:")) # Ключ активации:
                self.label_prompt.set_halign(Gtk.Align.START)
                self.vbox.pack_start(self.label_prompt, True, True, 0)


                # Activation key input field
                self.keybox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
                self.entry_keys = []
                previous_key_parts = ["","","","",""]
                if previously_inputed_license_key != "":
                        previous_key_parts = previously_inputed_license_key.split("-")
                for index in range(0, 5, 1):
                        if index > 0 :
                                label_key_sep = Gtk.Label()
                                label_key_sep.set_text("-")
                                self.keybox.pack_start(label_key_sep, True, True, 0)

                        entry_key = Gtk.Entry()
                        entry_key.set_text(previous_key_parts[index])
                        entry_key.set_width_chars(5)
                        entry_key.set_max_length(5)
                        entry_key.key_index = index
                        entry_key.connect("changed", self.on_entry_key_changed)
                        entry_key.connect("key-press-event", self.on_entry_key_press)
                        entry_key.connect("paste-clipboard", self.on_entry_key_paste_clipboard)
                        self.keybox.pack_start(entry_key, True, True, 0)
                        self.entry_keys.append(entry_key)

                self.vbox.pack_start(self.keybox, True, True, 0)

                # Activation button
                self.button_activate = Gtk.Button.new_with_label(_("Активировать")) # Активировать
                self.button_activate.connect("clicked", self.on_activate_clicked)
                self.vbox.pack_start(self.button_activate, True, True, 0)

                is_trial_button_enabled = True
                if trial_start_timestamp_str != "":
                        if is_trial_expired:
                                trial_button_label = _("Пробный период окончен") # Пробный период окончен
                                is_trial_button_enabled = False
                        else:
                                trial_button_label = _("Пробный период активирован") # Пробный период активирован
                                is_trial_button_enabled = False
                else:
                        trial_button_label = _("Получить пробную версию на 7 дней") # Получить пробную версию на 7 дней
                self.button_trial = Gtk.Button.new_with_label(trial_button_label)
                self.button_trial.connect("clicked", self.on_request_trial_clicked)
                self.vbox.pack_start(self.button_trial, True, True, 0)
                if is_trial_button_enabled == False:
                        self.button_trial.set_sensitive(False)

                # Support and purchase buttons
                self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                self.vbox.add(self.hbox)
                self.button_support = Gtk.LinkButton(uri=SUPPORT_URL, label=_("Техподдержка")) # Техподдержка
                self.hbox.pack_start(self.button_support, True, True, 0)
                self.button_purchase = Gtk.LinkButton(uri=PURCHASE_URL, label=_("Купить лицензию")) # Купить лицензию
                self.hbox.pack_start(self.button_purchase, True, True, 0)

                self.show_all()

        def on_entry_key_changed(self, widget):
                key_part = widget.get_text()
                if len(key_part) >= 5 and widget.key_index < 4 :
                        self.entry_keys[widget.key_index+1].grab_focus()

        def on_entry_key_press(self, widget, ev, data=None):
                key_part = widget.get_text()
                if len(key_part) == 0 and widget.key_index > 0 and  ev.keyval == Gdk.KEY_BackSpace:
                        entry_key = self.entry_keys[widget.key_index-1]
                        entry_key.grab_focus()
                        entry_key.set_position(len(entry_key.get_text()))

        def on_entry_key_paste_clipboard(self, widget):
                clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                text = clip.wait_for_text()
                text = text.replace('-', '')
                text = text.replace('\n', '')
                text = text.replace('\r', '')
                text = text.replace('\t', '')
                text = text.replace(' ', '')
                if text is not None:
                        key_part = widget.get_text()
                        text = key_part + text
                        for index in range(widget.key_index, 5, 1):
                                entry_key = self.entry_keys[index]
                                if len(text) > 5 :
                                        entry_key.set_text(text[:5])
                                        text = text[5:]
                                        if index == 4:
                                                entry_key.grab_focus()
                                                entry_key.set_position(len(entry_key.get_text()))
                                else:
                                        entry_key.set_text(text)
                                        entry_key.grab_focus()
                                        entry_key.set_position(len(entry_key.get_text()))
                                        break


        def on_activate_clicked(self, button):
                global window, destroy_handler
                result = activate(get_full_key(self), get_machine_hash())
                if result:
                        EXIT_CODE = 0
                        Gtk.main_quit()

        def on_request_trial_clicked(self, button):
                global window, destroy_handler
                result = start_trial(get_machine_hash())
                if result:
                        EXIT_CODE = 0
                        Gtk.main_quit()

class ReviewKeyWindow(Gtk.Window):
        def __init__(self):
                super().__init__(title=_("Активация Uncom OS")) # Активация Uncom OS
                self.set_border_width(10)
                self.set_default_size(500, 150)
                self.set_resizable(False)
                self.set_position(Gtk.WindowPosition.CENTER)

                # Main window container
                self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                self.add(self.vbox)

                icon_pixbuf_list = get_icon_pixbuf_list(ICON_NAME)
                if len(icon_pixbuf_list)!=0:
                        self.set_default_icon_list(icon_pixbuf_list)
                        #icon = Gtk.Image.new_from_pixbuf(icon_pixbuf_list[-1:][0])
                        #self.vbox.pack_start(icon, False, False, 0)

                # Messages
                label_message = Gtk.Label()
                label_message.set_text(_("Ваша версия операционной системы успешно активирована.")) # Ваша версия операционной системы успешно активирована.
                label_message.set_halign(Gtk.Align.START)
                label_message.set_line_wrap(True)
                self.vbox.pack_start(label_message, True, True, 0)

                # Activation key label
                self.label_prompt = Gtk.Label()
                self.label_prompt.set_text(_("Ключ активации:")) # Ключ активации:
                self.label_prompt.set_halign(Gtk.Align.START)
                self.vbox.pack_start(self.label_prompt, True, True, 0)

                # Activation key input field
                self.entry_key = Gtk.Entry()
                self.entry_key.set_text("")
                self.entry_key.set_sensitive(False)
                self.entry_key.set_text(stored_license_key)
                self.entry_key.set_alignment(xalign=0.5)
                self.vbox.pack_start(self.entry_key, True, True, 0)

                # Activation button
                self.button_deactivate = Gtk.Button.new_with_label(_("Деактивировать")) # Деактивировать
                self.button_deactivate.connect("clicked", self.on_deactivate_clicked)
                self.vbox.pack_start(self.button_deactivate, True, True, 0)

                # support button
                self.button_support = Gtk.LinkButton(uri=SUPPORT_URL, label=_("Техподдержка")) # Техподдержка
                self.vbox.pack_start(self.button_support, True, True, 0)

                self.show_all()

        def on_deactivate_clicked(self, button):
                global stored_license_key
                result = deactivate(stored_license_key)
                if result:
                        switch_to_request_key()

def get_icon_pixbuf_list(icon_name):
        icon_theme = Gtk.IconTheme.get_default()
        icon_pixbuf_list = list()
        sizes = icon_theme.get_icon_sizes(icon_name)
        sizes.sort()
        for size in sizes:
                pixbuf = icon_theme.load_icon(icon_name, size, 0)
                icon_pixbuf_list.append(pixbuf)
                #print(str(size))
        return icon_pixbuf_list

def get_full_key(window):
        full_key = "-".join([window.entry_keys[0].get_text(),
                             window.entry_keys[1].get_text(),
                             window.entry_keys[2].get_text(),
                             window.entry_keys[3].get_text(),
                             window.entry_keys[4].get_text()])
        return full_key

def get_machine_hash():
        print("Getting machine hardware hash...")
        if os.path.isfile(PATH_TO_UUID):
                print("File of UUID exists, checking it contents...")
                with open(PATH_TO_UUID, encoding="utf-8") as file:
                        uuid = file.read()
                        uuid_data = uuid.split(":", 1)
                        type = uuid_data[0]
                        hash = uuid_data[1].split(" ", 1)[0]
                        print("Hardware type: " + str(hash))
                        print("Hardware hash: " + str(hash))
                        file.close()
        else:
                print("File of UUID does not exist, using previous method...")
                descr = platform.machine() + ", " + platform.processor()
                hash = hashlib.sha256(str.encode(str(descr), "utf-8")).hexdigest()
                print("Hardware description: " + str(descr))
                print("Hardware hash: " + str(hash))

        return hash

def activate(license_key, machine_hash):
        global stored_license_key
        if license_key == "":
                show_message_empty_key()
                return False

        json_data = {"activation_key": license_key, "hardware_hash": machine_hash}
        print(json_data)

        try:
                r = requests.post(LICENSE_SERVER_URL + "activate_key", json=json_data)
                print("Server response for activate_key: " + str(r.headers) + " " + str(r.json()))
                if r.json()["is_activated"] == True:
                        with open(PATH_TO_KEY_FILE, "w", encoding="utf-8") as file:
                                file.write(license_key)
                                file.close()
                        stored_license_key = license_key
                        show_message_activated()
                        return True
                else:
                        show_message_broken_key()
                        return False
        except Exception as e:
                print("Error sending data to server (activate): " + str(e))
                show_message_connection_problem()
                return False
        
def start_trial(machine_hash):
        json_data = {"hardware_hash": machine_hash}
        print(json_data)

        try:
                r = requests.post(LICENSE_SERVER_URL + "check_trial", json=json_data)
                print("Server response for check_trial: " + str(r.headers) + " " + str(r.json()))
                if r.json()["is_trial_valid"] == True:
                        with open(PATH_TO_TRIAL_FILE, "w", encoding="utf-8") as file:
                                file.write("trial-local-start-timestamp=" + str(datetime.datetime.now().timestamp()))
                                file.close()
                        show_message_trial_started()
                        return True
                else:
                        show_message_trial_not_available()
                        return False
        except Exception as e:
                print("Error sending data to server (start_trial): " + str(e))
                show_message_connection_problem()
                return False

def deactivate(license_key):
        global stored_license_key, previously_inputed_license_key
        if license_key == "":
                show_message_empty_key()
                return False

        json_data = {"activation_key": license_key}
        print(json_data)

        try:
                r = requests.post(LICENSE_SERVER_URL + "deactivate_key", json=json_data)
                print("Server response for deactivate_key: " + str(r.headers) + " " + str(r.json()))
                if r.json()["is_deactivated"] == True:
                        with open(PATH_TO_KEY_FILE, "w", encoding="utf-8") as file:
                                file.write("")
                                file.close()
                        previously_inputed_license_key = license_key
                        stored_license_key = ""
                        show_message_deactivated()
                        return True
                else:
                        show_message_unable_to_deactivate()
                        return False
        except Exception as e:
                print("Error sending data to server (deactivate): " + str(e))
                show_message_connection_problem()
                return False

def check_activation(license_key, machine_hash):
        if license_key == "":
                return False

        json_data = {"activation_key": license_key, "hardware_hash": machine_hash}
        print(json_data)

        try:
                r = requests.post(LICENSE_SERVER_URL + "check_key", json=json_data)
                print("Server response for check_key: " + str(r.headers) + " " + str(r.json()))
                if r.json()["is_activation_valid"] == True:
                        return True
                else:
                        return False

        except Exception as e:
                print("Error sending data to server (check activation): " + str(e))
                print("No internet: skipping checking license till next autostart")
                return True
        
def check_trial(machine_hash):
        if machine_hash == "":
                return False

        json_data = {"hardware_hash": machine_hash}
        print(json_data)

        try:
                r = requests.post(LICENSE_SERVER_URL + "check_trial", json=json_data)
                print("Server response for check_trial: " + str(r.headers) + " " + str(r.json()))
                if r.json()["is_trial_valid"] == True:
                        return True
                else:
                        return False

        except Exception as e:
                print("Error sending data to server (check trial): " + str(e))
                print("No internet: skipping checking trial till next autostart")
                return True

def show_message_activated():
        dialog = Gtk.MessageDialog(
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=_("Активация успешна"), # Активация успешна
        )
        dialog.format_secondary_text(
            _("Спасибо, активация прошла успешно! Желаем приятного использования Uncom OS.") # Спасибо, активация прошла успешно! Желаем приятного использования Uncom OS.
        )
        dialog.run()
        dialog.destroy()

def show_message_trial_started():
        dialog = Gtk.MessageDialog(
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=_("Пробная версия активирована"), # Пробная версия активирована
        )
        dialog.format_secondary_text(
            _("Спасибо, пробная версия успешно активирована! Желаем приятного использования Uncom OS.") # Спасибо, пробная версия успешно активирована! Желаем приятного использования Uncom OS.
        )
        dialog.run()
        dialog.destroy()

def show_message_trial_not_available():
        dialog = Gtk.MessageDialog(
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=_("Пробная версия недоступна"), # Активация успешна
        )
        dialog.format_secondary_text(
            _("Пробная версия уже была ранее активирована на данном компьютере и закончилась по времени. Пожалуйста, введите ключ активации или обратитесь в поддержку Uncom OS.") # Пробная версия уже была ранее активирована на данном компьютере и закончилась по времени. Пожалуйста, введите ключ активации или обратитесь в поддержку Uncom OS.
        )
        dialog.run()
        dialog.destroy()

def show_message_deactivated():
        dialog = Gtk.MessageDialog(
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=_("Деактивация успешна"), # Деактивация успешна
        )
        dialog.format_secondary_text(
            _("Деактивация прошла успешно! Ключ активации теперь можно использовать на другом компьютере.") # Деактивация прошла успешно! Ключ активации теперь можно использовать на другом компьютере.
        )
        dialog.run()
        dialog.destroy()

def show_message_broken_key():
        dialog = Gtk.MessageDialog(
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=_("Неверный ключ"), # Неверный ключ
        )
        dialog.format_secondary_text(
            _("Введен неверный ключ. Пожалуйста, перепроверьте введенные данные. В случае продолжения проблем обратитесь в поддержку Uncom OS.") # Введен неверный ключ. Пожалуйста, перепроверьте введенные данные. В случае продолжения проблем обратитесь в поддержку Uncom OS.
        )
        dialog.run()
        dialog.destroy()

def show_message_unable_to_deactivate():
        dialog = Gtk.MessageDialog(
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=_("Невозможно деактивировать"), # Невозможно деактивировать
        )
        dialog.format_secondary_text(
            _("Невозможно деактивировать ключ. Возможно он был заблокирован. Пожалуйста, обратитесь в поддержку Uncom OS.") # Невозможно деактивировать ключ. Возможно он был заблокирован. Пожалуйста, обратитесь в поддержку Uncom OS.
        )
        dialog.run()
        dialog.destroy()

def show_message_empty_key():
        dialog = Gtk.MessageDialog(
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=_("Ключ не введен"), # Ключ не введен
        )
        dialog.format_secondary_text(
            _("Не введен ключ. Пожалуйста, введите активационный ключ Uncom OS.") # Не введен ключ. Пожалуйста, введите активационный ключ Uncom OS.
        )
        dialog.run()
        dialog.destroy()

def show_message_connection_problem():
        dialog = Gtk.MessageDialog(
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=_("Проблема соединения"), # Проблема соединения
        )
        dialog.format_secondary_text(
            _("Пожалуйста, проверьте соединение с интернетом. Если проблема повторяется, попробуйте позже или обратитесь в поддержку Uncom OS.") # Пожалуйста, проверьте соединение с интернетом. Если проблема повторяется, попробуйте позже или обратитесь в поддержку Uncom OS.
        )
        dialog.run()
        dialog.destroy()

def show_message_requires_reactivation():
        dialog = Gtk.MessageDialog(
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=_("Проблема проверки активации"), # Проблема проверки активации
        )
        dialog.format_secondary_text(
            _("Похоже, что данный ключ был активирован на другом устройстве. Его можно активировав на этом компьютере снова, тогда другое устройство будет отвязано.") # Похоже, что данный ключ был активирован на другом устройстве. Его можно активировав на этом компьютере снова, тогда другое устройство будет отвязано.
        )
        dialog.run()
        dialog.destroy()

def show_message_trial_expired():
        dialog = Gtk.MessageDialog(
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=_("Пробный период закончился"), # Пробный период закончился
        )
        dialog.format_secondary_text(
            _("Пробный период закончился. Для продолжения работы требуется ввести ключ активации.") # Пробный период закончился. Для продолжения работы требуется ввести ключ активации.
        )
        dialog.run()
        dialog.destroy()


def switch_to_review_key():
        global window, destroy_handler
        window.disconnect(destroy_handler)
        window.destroy()
        window = ReviewKeyWindow()
        destroy_handler = window.connect("destroy", Gtk.main_quit)

def switch_to_request_key():
        global window, destroy_handler
        window.disconnect(destroy_handler)
        window.destroy()
        window = RequestKeyWindow()
        destroy_handler = window.connect("destroy", Gtk.main_quit)

# Main program loop
window = None
destroy_handler = None
stored_license_key = ""
trial_start_timestamp_str = ""
is_trial_expired = False
previously_inputed_license_key = ""

if os.path.isfile(PATH_TO_KEY_FILE):
        print("License file exists, checking it contents...")
        with open(PATH_TO_KEY_FILE, encoding="utf-8") as file:
                stored_license_key = file.read()
                file.close()

if os.path.isfile(PATH_TO_TRIAL_FILE):
        print("Trial file exists, checking it contents...")
        with open(PATH_TO_TRIAL_FILE, encoding="utf-8") as file:
                trial_file_content = file.read()
                if trial_file_content != "":
                        trial_start_timestamp_str = trial_file_content.split("=", 1)[1]
                else:
                        trial_start_timestamp_str = ""
                file.close()

# Check activation

if stored_license_key == "":
        print("Current license: " + "n/a")
        if trial_start_timestamp_str == "":
                if (len(sys.argv) >= 2 and sys.argv[1] == "--check-license-bg"):
                        print("No activation or trial found, running in background, exit application with status code")
                        EXIT_CODE = 1
                        exit(EXIT_CODE)
                window = RequestKeyWindow()
                destroy_handler = window.connect("destroy", Gtk.main_quit)
        else:
                print("Checking availability of trial...")
                if (len(sys.argv) >= 2 and sys.argv[1] == "--check-license-bg"):
                        is_trial_activated = check_trial(get_machine_hash())
                        if is_trial_activated:
                                print("Trial is valid")
                                EXIT_CODE = 0
                                exit(EXIT_CODE)
                        else:
                                print("Trial is expired")
                                EXIT_CODE = 1
                                exit(EXIT_CODE)
                elif (len(sys.argv) >= 2 and sys.argv[1] == "--check-license"):
                        is_trial_activated = check_trial(get_machine_hash())
                        if is_trial_activated:
                                print("Trial is valid")
                                EXIT_CODE = 0
                                exit(EXIT_CODE)
                        else:
                                is_trial_expired = True
                                print("Trial is expired, show interface")
                                EXIT_CODE = 1
                                window = RequestKeyWindow()
                                destroy_handler = window.connect("destroy", Gtk.main_quit)
                                show_message_trial_expired()
                else:
                        is_trial_activated = check_trial(get_machine_hash())
                        if is_trial_activated == False:
                                is_trial_expired = True
                        window = RequestKeyWindow()
                        destroy_handler = window.connect("destroy", Gtk.main_quit)
else:
        print("Current license: " + stored_license_key)
        previously_inputed_license_key = stored_license_key
        if (len(sys.argv) >= 2 and sys.argv[1] == "--check-license-bg"):
                is_activated = check_activation(stored_license_key, get_machine_hash())
                if is_activated:
                        print("Activation is checked successfully")
                        EXIT_CODE = 0
                        exit(EXIT_CODE)
                else:
                        print("No activation found")
                        EXIT_CODE = 1
                        exit(EXIT_CODE)
        elif (len(sys.argv) >= 2 and sys.argv[1] == "--check-license"):
                is_activated = check_activation(stored_license_key, get_machine_hash())
                if is_activated:
                        print("Activation is checked successfully")
                        EXIT_CODE = 0
                        exit(EXIT_CODE)
                else:
                        print("No activation found, show interface")
                        if trial_start_timestamp_str != "":
                                is_trial_expired = True
                        EXIT_CODE = 1
                        window = RequestKeyWindow()
                        destroy_handler = window.connect("destroy", Gtk.main_quit)
                        show_message_requires_reactivation()
        else:
                if trial_start_timestamp_str != "":
                        is_trial_expired = True
                EXIT_CODE = 0
                window = ReviewKeyWindow()
                destroy_handler = window.connect("destroy", Gtk.main_quit)

Gtk.main()
print("EXIT_CODE =", EXIT_CODE)
exit(EXIT_CODE)
