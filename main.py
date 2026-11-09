import os
import subprocess
import sys
import json
import threading
import urllib.request

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window

CONFIG_FILE = "saved_links.json"
DOWNLOAD_DIR = "downloaded_scripts"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def load_links():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_links(links):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=4)

class MainPanel(BoxLayout):
    def __init__(self, app_instance, **kwargs):
        super(MainPanel, self).__init__(**kwargs)
        self.app_instance = app_instance
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        # Title bar
        title_layout = BoxLayout(size_hint_y=None, height=40)
        title_lbl = Label(text="[b]QUẢN LÝ & CHẠY PYTHON[/b]", markup=True, color=(1, 1, 1, 1))
        close_btn = Button(text="✕", size_hint_x=None, width=40, background_color=(0.8, 0.2, 0.2, 1))
        close_btn.bind(on_press=self.close_panel)
        title_layout.add_widget(title_lbl)
        title_layout.add_widget(close_btn)
        self.add_widget(title_layout)

        # Action buttons row 1
        row1 = BoxLayout(size_hint_y=None, height=45, spacing=5)
        btn_add_git = Button(text="🌐 Thêm Git", background_color=(0.9, 0.6, 0.1, 1))
        btn_add_git.bind(on_press=self.add_git_popup)
        btn_stop = Button(text="⏹ Dừng", background_color=(0.8, 0.2, 0.2, 1))
        btn_stop.bind(on_press=lambda x: self.app_instance.stop_current_process())
        row1.add_widget(btn_add_git)
        row1.add_widget(btn_stop)
        self.add_widget(row1)

        # Scrollable file list
        self.scroll = ScrollView()
        self.list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        self.add_widget(self.scroll)

        # Output console
        self.output_box = TextInput(text="Kết quả thực thi sẽ hiển thị ở đây...\n", readonly=True, background_color=(0.1, 0.1, 0.1, 1), foreground_color=(0, 1, 0, 1), size_hint_y=None, height=150)
        self.add_widget(self.output_box)

        self.refresh_file_list()

    def close_panel(self, instance):
        self.app_instance.root_layout.remove_widget(self)
        self.app_instance.panel_open = False

    def refresh_file_list(self):
        self.list_layout.clear_widgets()

        # List Auto files
        for f in sorted(os.listdir('.')):
            if f.lower().startswith('auto') and f.endswith('.py'):
                row = BoxLayout(size_hint_y=None, height=40, spacing=5)
                btn_run = Button(text=f"▶ {f}", background_color=(0.2, 0.7, 0.3, 1))
                btn_run.bind(on_press=lambda x, path=f: self.app_instance.run_path(path))
                row.add_widget(btn_run)
                self.list_layout.add_widget(row)

        # List Saved Links
        links = load_links()
        for name, path in links.items():
            row = BoxLayout(size_hint_y=None, height=40, spacing=5)
            btn_run = Button(text=f"▶ {name}", background_color=(0, 0.5, 0.8, 1))
            btn_run.bind(on_press=lambda x, p=path: self.app_instance.run_path(p))
            row.add_widget(btn_run)
            self.list_layout.add_widget(row)

    def add_git_popup(self, instance):
        self.app_instance.log("Vui lòng thêm link git trực tiếp qua code hoặc cấu hình.")

class PythonManagerApp(App):
    def build(self):
        self.title = "Python Auto Manager"
        self.current_process = None
        self.panel_open = False

        self.root_layout = FloatLayout()

        # Floating Button (Bong bóng)
        self.float_btn = Button(text="💬 BONG BÓNG", size_hint=(None, None), size=(140, 45), pos=(50, 50), background_color=(1, 0.6, 0, 1))
        self.float_btn.bind(on_release=self.toggle_panel)
        self.root_layout.add_widget(self.float_btn)

        return self.root_layout

    def toggle_panel(self, instance):
        if not self.panel_open:
            self.panel = MainPanel(self, size_hint=(0.9, 0.8), pos_hint={'center_x': 0.5, 'center_y': 0.5})
            self.root_layout.add_widget(self.panel)
            self.panel_open = True
        else:
            self.root_layout.remove_widget(self.panel)
            self.panel_open = False

    def log(self, text):
        print(text)
        if hasattr(self, 'panel') and hasattr(self.panel, 'output_box'):
            self.panel.output_box.text += text + "\n"

    def run_path(self, p):
        p = p.strip().strip('"').strip("'")
        if not p or not os.path.exists(p):
            self.log(f"Không tìm thấy đường dẫn: {p}")
            return
        
        if self.current_process:
            self.stop_current_process()

        self.log(f"Đang chạy: {p}")
        
        def target():
            try:
                self.current_process = subprocess.Popen(
                    [sys.executable, p],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8"
                )
                stdout, stderr = self.current_process.communicate()
                if stdout:
                    Clock.schedule_once(lambda dt: self.log(stdout))
                if stderr:
                    Clock.schedule_once(lambda dt: self.log(f"[LỖI]:\n{stderr}"))
                Clock.schedule_once(lambda dt: self.log("[Hoàn tất!]"))
            except Exception as ex:
                Clock.schedule_once(lambda dt: self.log(f"Lỗi thực thi: {str(ex)}"))
            finally:
                self.current_process = None

        threading.Thread(target=target, daemon=True).start()

    def stop_current_process(self):
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process = None
                self.log("❌ [Đã dừng tiến trình]")
            except Exception as e:
                self.log(f"Lỗi dừng: {e}")
        else:
            self.log("⚠️ Không có tiến trình nào đang chạy.")

if __name__ == '__main__':
    PythonManagerApp().run()
