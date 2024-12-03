import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
from threading import Thread
import time


class SerialApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WiFi Configurator")

        # Variables
        self.selected_port = tk.StringVar()
        self.baudrate = tk.StringVar(value="9600")  # Default baud rate
        self.ssid = tk.StringVar()
        self.password = tk.StringVar()
        self.serial_connection = None

        # COM Port Dropdown
        ttk.Label(root, text="COM Port:").grid(row=0, column=0, padx=10, pady=5)
        self.combobox = ttk.Combobox(root, textvariable=self.selected_port, state="readonly")
        self.combobox.grid(row=0, column=1, padx=10, pady=5)
        self.refresh_com_ports()

        # Refresh Button
        ttk.Button(root, text="Refresh", command=self.refresh_com_ports).grid(row=0, column=2, padx=10, pady=5)

        # Baud Rate Dropdown
        ttk.Label(root, text="Baud Rate:").grid(row=1, column=0, padx=10, pady=5)
        self.baudrate_combobox = ttk.Combobox(
            root, textvariable=self.baudrate, state="readonly", values=["9600", "19200", "38400", "57600", "115200"]
        )
        self.baudrate_combobox.grid(row=1, column=1, padx=10, pady=5)

        # SSID Entry
        ttk.Label(root, text="SSID:").grid(row=2, column=0, padx=10, pady=5)
        ttk.Entry(root, textvariable=self.ssid).grid(row=2, column=1, padx=10, pady=5)

        # Password Entry
        ttk.Label(root, text="Password:").grid(row=3, column=0, padx=10, pady=5)
        ttk.Entry(root, textvariable=self.password, show="*").grid(row=3, column=1, padx=10, pady=5)

        # Connect Button
        ttk.Button(root, text="Connect", command=self.connect_to_serial).grid(row=4, column=0, pady=10)

        # Send Button
        ttk.Button(root, text="Send", command=self.send_to_serial).grid(row=4, column=1, pady=10)

        # Disconnect Button
        ttk.Button(root, text="Disconnect", command=self.disconnect_serial).grid(row=4, column=2, pady=10)

        # Serial Monitor Text Area
        ttk.Label(root, text="Serial Monitor:").grid(row=5, column=0, columnspan=3, padx=10, pady=5)
        self.text_area = tk.Text(root, height=15, width=60, state="disabled")
        self.text_area.grid(row=6, column=0, columnspan=3, padx=10, pady=5)

        # Start serial listener thread
        self.running = True
        self.listener_thread = Thread(target=self.serial_listener, daemon=True)
        self.listener_thread.start()

    def refresh_com_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.combobox["values"] = ports
        if ports:
            self.selected_port.set(ports[0])
        else:
            self.selected_port.set("")

    def connect_to_serial(self):
        if not self.selected_port.get():
            self.update_text_area("No COM port selected.\n")
            return

        try:
            if not self.serial_connection or not self.serial_connection.is_open:
                self.serial_connection = serial.Serial(
                    self.selected_port.get(),
                    baudrate=int(self.baudrate.get()),
                    timeout=1,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                )
                self.update_text_area(f"Connected to {self.selected_port.get()} at {self.baudrate.get()} baud.\n")
        except Exception as e:
            self.update_text_area(f"Error: {e}\n")

    def send_to_serial(self):
        if not self.serial_connection or not self.serial_connection.is_open:
            self.update_text_area("Not connected to any COM port.\n")
            return

        if not self.ssid.get() or not self.password.get():
            self.update_text_area("SSID and Password cannot be empty.\n")
            return

        try:
            message = f"setWifi - '{self.ssid.get()}' --'{self.password.get()}'\n"
            self.serial_connection.write(message.encode())
            self.update_text_area(f"Sent: {message}")
        except Exception as e:
            self.update_text_area(f"Error: {e}\n")

    def disconnect_serial(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.update_text_area("Disconnected from the COM port.\n")
        else:
            self.update_text_area("No active connection to disconnect.\n")

    def serial_listener(self):
        while self.running:
            if self.serial_connection and self.serial_connection.is_open:
                try:
                    raw_data = self.serial_connection.readline()
                    try:
                        # Attempt to decode the data as UTF-8
                        line = raw_data.decode('utf-8', errors='replace').strip()
                    except Exception:
                        # Fallback to raw hexadecimal representation
                        line = f"Raw: {raw_data.hex()}"
                    if line:
                        self.update_text_area(f"Received: {line}\n")
                except Exception as e:
                    self.update_text_area(f"Listener Error: {e}\n")
            time.sleep(0.1)

    def update_text_area(self, message):
        self.text_area.config(state="normal")
        self.text_area.insert("end", message)
        self.text_area.see("end")
        self.text_area.config(state="disabled")

    def close_app(self):
        self.running = False
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SerialApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.mainloop()
