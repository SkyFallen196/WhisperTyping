import customtkinter as ctk
import threading
from pynput import keyboard
import codecs
import time
import pyaudio
import wave
import os
from playsound import playsound
from datetime import datetime
from groq import Groq
from PIL import Image
import pystray
import json

# Set theme and color scheme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SettingsDialog:
    def __init__(self, parent):
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.resizable(False, False)
        
        # Load current API key
        with open('settings.json', 'r') as f:
            self.settings = json.load(f)
        
        # API Key input
        self.api_frame = ctk.CTkFrame(self.dialog)
        self.api_frame.pack(fill="x", padx=20, pady=20)
        
        self.api_label = ctk.CTkLabel(
            self.api_frame,
            text="Groq API Key:",
            font=ctk.CTkFont(size=14)
        )
        self.api_label.pack(anchor="w", pady=5)
        
        self.api_entry = ctk.CTkEntry(
            self.api_frame,
            width=300,
            font=ctk.CTkFont(size=14)
        )
        self.api_entry.pack(pady=5)
        self.api_entry.insert(0, self.settings.get('api_key', ''))
        
        # Save button
        self.save_btn = ctk.CTkButton(
            self.dialog,
            text="Save",
            command=self.save_settings,
            width=100
        )
        self.save_btn.pack(pady=20)
        
    def save_settings(self):
        self.settings['api_key'] = self.api_entry.get()
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f)
        self.dialog.destroy()

class WhisperTypingApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("WhisperTyping")
        self.root.geometry("400x250")
        self.root.minsize(400, 250)
        
        # Initialize variables
        self.is_recording = False
        self.file_ready_counter = 0
        self.stop_recording = False
        self.pykeyboard = keyboard.Controller()
        self.recording_animation_active = False
        
        # Try to load settings and initialize Groq
        try:
            self.load_settings()
        except Exception:
            # Show settings dialog immediately if API key is missing or invalid
            self.setup_ui()  # Setup UI first
            self.show_api_key_error()
            
        # Initialize system tray
        self.setup_system_tray()
        
        # Track if log section is expanded
        self.log_expanded = False  # Start with log collapsed
        
        # Global keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.keyboard_listener.start()
        
        self.setup_ui()
        self.start_transcription_thread()
        
    def show_api_key_error(self):
        error_dialog = ctk.CTkToplevel(self.root)
        error_dialog.title("API Key Error")
        error_dialog.geometry("400x200")
        error_dialog.transient(self.root)
        error_dialog.resizable(False, False)
        
        # Center the dialog
        error_dialog.geometry("+%d+%d" % (
            self.root.winfo_x() + (self.root.winfo_width() - 400) // 2,
            self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        ))
        
        # Error message
        message = ctk.CTkLabel(
            error_dialog,
            text="Invalid Groq API Key detected.\nPlease enter a valid API key to continue.",
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        message.pack(pady=20)
        
        # API Key input
        api_entry = ctk.CTkEntry(
            error_dialog,
            width=300,
            font=ctk.CTkFont(size=14)
        )
        api_entry.pack(pady=10)
        api_entry.insert(0, self.settings.get('api_key', ''))
        
        def save_and_retry():
            new_key = api_entry.get()
            try:
                self.groq_client = Groq(api_key=new_key)
                self.settings['api_key'] = new_key
                with open('settings.json', 'w') as f:
                    json.dump(self.settings, f)
                error_dialog.destroy()
                self.status_label.configure(text="API Key updated successfully!")
            except Exception:
                message.configure(text="Invalid API Key. Please try again.", text_color="red")
        
        # Save button
        save_btn = ctk.CTkButton(
            error_dialog,
            text="Save & Retry",
            command=save_and_retry,
            width=120
        )
        save_btn.pack(pady=20)
        
    def show_error(self, error_message):
        self.status_label.configure(
            text=error_message,
            text_color="red"
        )
        
    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            self.settings = {'api_key': ''}

        api_key = self.settings.get('api_key', '')
        if not api_key:
            raise Exception("API key not set")

        self.groq_client = Groq(api_key=api_key)
        
    def setup_system_tray(self):
        # Create system tray icon
        self.icon_image = Image.new('RGB', (64, 64), color='blue')
        self.tray_icon = pystray.Icon(
            "Voice Typer",
            self.icon_image,
            menu=pystray.Menu(
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Exit", self.quit_app)
            )
        )
        
    def setup_ui(self):
        # Main container with padding
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header frame with title and settings button
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=5)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="WhisperTyping",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(side="left", padx=10)
        
        # Settings button
        self.settings_btn = ctk.CTkButton(
            self.header_frame,
            text="⚙️",
            width=40,
            command=self.open_settings
        )
        self.settings_btn.pack(side="right", padx=10)
        
        # Record button and indicator in one frame
        self.control_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.control_frame.pack(fill="x", pady=10)
        
        self.record_button = ctk.CTkButton(
            self.control_frame,
            text="Start Recording (Insert)",
            command=self.toggle_recording,
            height=40,
            corner_radius=20
        )
        self.record_button.pack(pady=5)
        
        self.recording_indicator = ctk.CTkProgressBar(
            self.control_frame,
            width=200,
            height=6
        )
        self.recording_indicator.pack(pady=5)
        self.recording_indicator.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="Ready to record...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
        
        # Create a container frame for log section
        self.log_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.log_container.pack(fill="x", expand=False)
        
        # Log controls in container
        self.toggle_log_btn = ctk.CTkButton(
            self.log_container,
            text="▶ Show Log",
            command=self.toggle_log_section,
            width=100,
            height=28,
            fg_color=["#2B2B2B", "#333333"],
            hover_color=["#333333", "#404040"]
        )
        self.toggle_log_btn.pack(side="left", padx=5)
        
        self.clear_log_btn = ctk.CTkButton(
            self.log_container,
            text="Clear",
            command=self.clear_logs,
            width=60,
            height=28,
            fg_color="#c93434",
            hover_color="#a82a2a"
        )
        self.clear_log_btn.pack(side="right", padx=5)
        
        # Log frame and content
        self.log_frame = ctk.CTkFrame(self.main_frame)
        self.transcription_text = ctk.CTkTextbox(
            self.log_frame,
            height=200,
            font=ctk.CTkFont(size=12)
        )
        self.transcription_text.pack(fill="both", expand=True, pady=5)
        
    def animate_recording(self):
        if self.recording_animation_active:
            current = self.recording_indicator.get()
            if current >= 1:
                self.recording_indicator.set(0)
            else:
                self.recording_indicator.set(current + 0.05)  # Smoother animation
            self.root.after(50, self.animate_recording)  # Faster updates
            
            # Pulse effect on record button
            current_color = self.record_button.cget("fg_color")
            if current_color == "#c93434":
                self.record_button.configure(fg_color="#a82a2a")
            else:
                self.record_button.configure(fg_color="#c93434")
    
    def toggle_recording(self):
        if not hasattr(self, 'groq_client'):
            self.show_api_key_error()
            return
            
        if not self.is_recording:
            self.start_recording()
            # Start animation with pulsing effect
            self.recording_animation_active = True
            self.record_button.configure(
                fg_color="#c93434",
                text="■ Stop Recording (Insert)"  # Square stop symbol
            )
            self.animate_recording()
        else:
            self.stop_recording = True
            # Stop animation
            self.recording_animation_active = False
            self.record_button.configure(
                fg_color=["#3B8ED0", "#1F6AA5"],
                text="● Start Recording (Insert)"  # Circle record symbol
            )
            self.recording_indicator.set(0)
    
    def on_key_press(self, key):
        try:
            if key == keyboard.Key.insert:
                self.root.after(0, self.toggle_recording)
        except AttributeError:
            pass
    
    def on_key_release(self, key):
        pass
            
    def start_recording(self):
        threading.Thread(target=self.record_speech, daemon=True).start()
        
    def record_speech(self):
        self.is_recording = True
        chunk = 1024
        sample_format = pyaudio.paInt16
        channels = 2
        fs = 44100
        
        p = pyaudio.PyAudio()
        stream = p.open(
            format=sample_format,
            channels=channels,
            rate=fs,
            frames_per_buffer=chunk,
            input=True
        )
        
        frames = []
        playsound("assets/on.wav")
        
        while not self.stop_recording:
            data = stream.read(chunk)
            frames.append(data)
            
        stream.stop_stream()
        stream.close()
        p.terminate()
        playsound("assets/off.wav")
        
        # Save recording
        wf = wave.open(f"test{self.file_ready_counter+1}.wav", 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(fs)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        self.stop_recording = False
        self.is_recording = False
        self.file_ready_counter += 1
        
        self.status_label.configure(text="Processing transcription...")
        
    def transcribe_audio(self, audio_file):
        with open(audio_file, 'rb') as audio:
            transcription = self.groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio
            )
            return transcription.text
            
    def start_transcription_thread(self):
        threading.Thread(target=self.transcribe_speech).start()
        
    def transcribe_speech(self):
        i = 1
        
        while True:
            while self.file_ready_counter < i:
                time.sleep(0.01)
                
            audio_file = f"test{i}.wav"
            try:
                transcript = self.transcribe_audio(audio_file)
                
                # Update GUI
                self.transcription_text.insert('1.0', f"{datetime.now().strftime('%H:%M:%S')}: {transcript}\n\n")
                self.status_label.configure(text="Ready to record...")
                
                # Log transcription
                with codecs.open('transcribe.log', 'a', encoding='utf-8') as f:
                    f.write(f"{datetime.now()}: {transcript}\n")
                    
                # Type the text
                for element in transcript:
                    try:
                        self.pykeyboard.type(element)
                        time.sleep(0.0025)
                    except:
                        print("empty or unknown symbol")
                        
                os.remove(audio_file)
                i += 1
                
            except Exception as e:
                self.status_label.configure(text=f"Error: {str(e)}")
                i += 1

    def __del__(self):
        # Clean up keyboard listener
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()

    def animate_window_resize(self, target_height, current_height=None, step=0):
        total_steps = 15  # Move this outside the if statement
        
        if current_height is None:
            current_height = self.root.winfo_height()
            height_diff = target_height - current_height
            self.height_step = height_diff / total_steps
        
        if step < total_steps:
            new_height = int(current_height + self.height_step)
            self.root.geometry(f"400x{new_height}")
            self.root.after(10, lambda: self.animate_window_resize(target_height, new_height, step + 1))
        else:
            self.root.geometry(f"400x{target_height}")
            # Ensure proper packing of log frame after animation
            if self.log_expanded:
                self.log_frame.pack(fill="both", expand=True, pady=5)
            else:
                self.log_frame.pack_forget()

    def toggle_log_section(self):
        if not hasattr(self, 'log_expanded'):
            self.log_expanded = False
            
        self.log_expanded = not self.log_expanded
        
        if self.log_expanded:
            self.toggle_log_btn.configure(
                text="▼ Hide Log",
                fg_color="#c93434",
                hover_color="#a82a2a"
            )
            self.log_frame.pack(fill="both", expand=True, pady=5)
            self.animate_window_resize(600)
        else:
            self.toggle_log_btn.configure(
                text="▶ Show Log",
                fg_color=["#2B2B2B", "#333333"],
                hover_color=["#333333", "#404040"]
            )
            self.log_frame.pack_forget()
            self.animate_window_resize(250)
            
    def clear_logs(self):
        self.transcription_text.delete('1.0', 'end')
        # Also clear the log file
        with open('transcribe.log', 'w', encoding='utf-8') as f:
            f.write('')
            
    def minimize_to_tray(self):
        self.root.withdraw()  # Hide the window
        if not self.tray_icon.visible:
            # Start system tray icon in a separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
    def show_window(self):
        self.tray_icon.stop()
        self.root.after(0, self.root.deiconify)
        
    def quit_app(self):
        self.tray_icon.stop()
        self.root.quit()

    def open_settings(self):
        SettingsDialog(self.root)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = WhisperTypingApp()
    app.run() 