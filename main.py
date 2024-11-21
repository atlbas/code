import asyncio
import tkinter as tk
from tkinter import ttk
from bleak import BleakClient, BleakScanner
from async_tkinter_loop import async_handler, async_mainloop
from datetime import datetime
import json
import os


class BLEApp:
    def __init__(self, root):
        self.root = root
        self.client = None
        self.device = None
        self.selected_device_id = None
        self.connected_device_name = None
        self.discovered_devices = {}

        self.load_config()

        self.root.title("BLE Client")
        self.root.geometry("1200x750")  # Увеличим ширину и высоту окна
        self.root.call('tk', 'scaling', 1.8)

        # Убедитесь, что основное поле растягивается
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=3)
        self.root.grid_columnconfigure(0, weight=1)

        self.frame = ttk.Frame(root, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.log_frame = ttk.Frame(root, padding="10")
        self.log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Убедитесь, что поле лога заполняет пространство
        self.log_text = tk.Text(self.log_frame, width=140, height=12, state='disabled', wrap='word', font=("Helvetica", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.scrollbar = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.log_text['yscrollcommand'] = self.scrollbar.set

        self.device_selection = ttk.Combobox(self.frame, values=list(self.devices.keys()), width=60)
        self.device_selection.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky='ew')
        self.device_selection.bind("<<ComboboxSelected>>", self.on_device_selected)

        self.connect_button = ttk.Button(self.frame, text="Connect", command=async_handler(self.connect))
        self.connect_button.grid(row=1, column=0, padx=5, pady=5, sticky='ew')

        self.read_button = ttk.Button(self.frame, text="Read", command=async_handler(self.read), state="disabled")
        self.read_button.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

        self.write_button = ttk.Button(self.frame, text="Write", command=async_handler(self.write), state="disabled")
        self.write_button.grid(row=1, column=2, padx=5, pady=5, sticky='ew')

        self.disconnect_button = ttk.Button(self.frame, text="Disconnect", command=async_handler(self.disconnect),
                                            state="disabled")
        self.disconnect_button.grid(row=1, column=3, padx=5, pady=5, sticky='ew')

        
        self.create_input_fields()

        
        self.status_label = ttk.Label(self.frame, text="Status: Not Connected")
        self.status_label.grid(row=12, column=0, columnspan=4, padx=5, pady=5,
                               sticky='ew')  # Переместим статус на 12 строку

        self.device_selection.set("00001")
        self.on_device_selected(None)

    def load_config(self):
        config_path = 'config.json'
        if not os.path.exists(config_path):
            self.devices = {
                "00001": {
                    "name": "ESP32_BLE",
                    "service_uuid": "4fafc201-1fb5-459e-8fcc-c5c9c331914b",
                    "characteristic_uuid": "beb5483e-36e1-4688-b7f5-ea07361b26a8",
                    "request_uuid": "c0de1234-5678-9abc-def0-123456789abc"
                }
            }
            with open(config_path, 'w') as f:
                json.dump(self.devices, f, indent=4)
        else:
            with open(config_path, 'r') as f:
                self.devices = json.load(f)

    def create_input_fields(self):
        
        self.name_label = ttk.Label(self.frame, text="Device Name: ")
        self.name_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(self.frame, textvariable=self.name_var, width=80, state='readonly')
        self.name_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky='ew')

        self.service_uuid_label = ttk.Label(self.frame, text="Service UUID: ")
        self.service_uuid_label.grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.service_uuid_var = tk.StringVar()
        self.service_uuid_entry = ttk.Entry(self.frame, textvariable=self.service_uuid_var, width=80, state='readonly')
        self.service_uuid_entry.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky='ew')

        self.characteristic_uuid_label = ttk.Label(self.frame, text="Characteristic UUID: ")
        self.characteristic_uuid_label.grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.characteristic_uuid_var = tk.StringVar()
        self.characteristic_uuid_entry = ttk.Entry(self.frame, textvariable=self.characteristic_uuid_var, width=80,
                                                   state='readonly')
        self.characteristic_uuid_entry.grid(row=4, column=1, columnspan=3, padx=5, pady=5, sticky='ew')

        self.request_uuid_label = ttk.Label(self.frame, text="Request UUID: ")
        self.request_uuid_label.grid(row=5, column=0, padx=5, pady=5, sticky='w')
        self.request_uuid_var = tk.StringVar()
        self.request_uuid_entry = ttk.Entry(self.frame, textvariable=self.request_uuid_var, width=80, state='readonly')
        self.request_uuid_entry.grid(row=5, column=1, columnspan=3, padx=5, pady=5, sticky='ew')

        self.longitude_label = ttk.Label(self.frame, text="Longitude: ")
        self.longitude_label.grid(row=6, column=0, padx=5, pady=5, sticky='w')
        self.longitude_var = tk.StringVar()
        self.longitude_entry = ttk.Entry(self.frame, textvariable=self.longitude_var, width=20)
        self.longitude_entry.grid(row=6, column=1, padx=5, pady=5, sticky='ew')

        self.cargo_id_label = ttk.Label(self.frame, text="Cargo ID: ")
        self.cargo_id_label.grid(row=6, column=2, padx=5, pady=5, sticky='w')
        self.cargo_id_var = tk.StringVar()
        self.cargo_id_entry = ttk.Entry(self.frame, textvariable=self.cargo_id_var, width=20)
        self.cargo_id_entry.grid(row=6, column=3, padx=5, pady=5, sticky='ew')

        self.latitude_label = ttk.Label(self.frame, text="Latitude: ")
        self.latitude_label.grid(row=7, column=0, padx=5, pady=5, sticky='w')
        self.latitude_var = tk.StringVar()
        self.latitude_entry = ttk.Entry(self.frame, textvariable=self.latitude_var, width=20)
        self.latitude_entry.grid(row=7, column=1, padx=5, pady=5, sticky='ew')

        self.address_label = ttk.Label(self.frame, text="Address: ")
        self.address_label.grid(row=8, column=0, padx=5, pady=5, sticky='w')
        self.address_var = tk.StringVar()
        self.address_entry = ttk.Entry(self.frame, textvariable=self.address_var, width=80)
        self.address_entry.grid(row=8, column=1, columnspan=3, padx=5, pady=5, sticky='ew')

        self.full_name_label = ttk.Label(self.frame, text="Full Name: ")
        self.full_name_label.grid(row=9, column=0, padx=5, pady=5, sticky='w')
        self.full_name_var = tk.StringVar()
        self.full_name_entry = ttk.Entry(self.frame, textvariable=self.full_name_var, width=80)
        self.full_name_entry.grid(row=9, column=1, columnspan=3, padx=5, pady=5, sticky='ew')

        self.price_label = ttk.Label(self.frame, text="Price: ")
        self.price_label.grid(row=10, column=0, padx=5, pady=5, sticky='w')
        self.price_var = tk.StringVar()
        self.price_entry = ttk.Entry(self.frame, textvariable=self.price_var, width=20)
        self.price_entry.grid(row=10, column=1, padx=5, pady=5, sticky='ew')

        self.weight_label = ttk.Label(self.frame, text="Weight: ")
        self.weight_label.grid(row=10, column=2, padx=5, pady=5, sticky='w')
        self.weight_var = tk.StringVar()
        self.weight_entry = ttk.Entry(self.frame, textvariable=self.weight_var, width=20)
        self.weight_entry.grid(row=10, column=3, padx=5, pady=5, sticky='ew')

        self.description_label = ttk.Label(self.frame, text="Description: ")
        self.description_label.grid(row=11, column=0, padx=5, pady=5, sticky='w')
        self.description_var = tk.StringVar()
        self.description_entry = ttk.Entry(self.frame, textvariable=self.description_var, width=80)
        self.description_entry.grid(row=11, column=1, columnspan=3, padx=5, pady=5, sticky='ew')

    def on_device_selected(self, event):
        selected_device = self.device_selection.get()
        if selected_device in self.devices:
            self.selected_device_id = selected_device
            device_info = self.devices[selected_device]
            self.service_uuid_var.set(device_info["service_uuid"])
            self.characteristic_uuid_var.set(device_info["characteristic_uuid"])
            self.request_uuid_var.set(device_info["request_uuid"])
            self.name_var.set(device_info["name"])

            if self.client and self.client.is_connected:
                asyncio.create_task(self.disconnect())
            self.log(f"Selected device: {selected_device} ({device_info['name']})")

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, log_message)
        self.log_text.configure(state='disabled')
        self.log_text.see(tk.END)

    async def connect(self):
        if self.client and self.client.is_connected:
            await self.disconnect()

        if not self.selected_device_id:
            self.status_label.config(text="Status: No device selected")
            self.log("No device selected")
            return

        selected_device_info = self.devices[self.selected_device_id]
        selected_device_name = selected_device_info["name"]

        self.log(f"Searching for {selected_device_name}...")

        try:
            if selected_device_name in self.discovered_devices:
                self.device = self.discovered_devices[selected_device_name]
                self.log(f"Using previously discovered device: {selected_device_name}")
            else:
                devices = await BleakScanner.discover(timeout=5.0)
                found_devices = []
                for device in devices:
                    if device.name:
                        self.discovered_devices[device.name] = device
                        found_devices.append(device.name)
                        if device.name == selected_device_name:
                            self.device = device
                            break

                self.log(f"Discovered devices: {', '.join(found_devices)}")

                if self.device is None:
                    self.status_label.config(text=f"Status: {selected_device_name} not found")
                    self.log(f"{selected_device_name} not found")
                    return

            self.client = BleakClient(self.device)
            try:
                await asyncio.wait_for(self.client.connect(), timeout=10.0)
            except asyncio.TimeoutError:
                raise Exception("Connection attempt timed out after 10 seconds")

            if self.client.is_connected:
                self.connected_device_name = self.device.name
                self.status_label.config(text=f"Status: Connected to {self.device.name}")
                self.read_button.config(state="normal")
                self.write_button.config(state="normal")
                self.disconnect_button.config(state="normal")
                self.log(f"Connected to {self.device.name}")
            else:
                raise Exception("Failed to establish connection")

        except Exception as e:
            error_message = f"Connection failed: {str(e)}"
            self.status_label.config(text=f"Status: {error_message}")
            self.log(error_message)

            if "timed out" in str(e).lower():
                self.log("Suggestion: Check if the device is powered on and in range")
            elif "failed to establish connection" in str(e).lower():
                self.log("Suggestion: Try restarting the Bluetooth on both devices")
            elif "not found" in str(e).lower():
                self.log("Suggestion: Ensure the device is in pairing mode")
            else:
                self.log("Suggestion: Check Bluetooth settings and device compatibility")

            self.client = None
            self.device = None
            self.connected_device_name = None

    async def disconnect(self):
        if self.client and self.client.is_connected:
            disconnected_device_name = self.connected_device_name or "Unknown device"
            self.log(f"Disconnecting from {disconnected_device_name}...")
            await self.client.disconnect()
            self.status_label.config(text=f"Status: Disconnected from {disconnected_device_name}")
            self.read_button.config(state="disabled")
            self.write_button.config(state="disabled")
            self.disconnect_button.config(state="disabled")
            self.client = None
            self.device = None
            self.connected_device_name = None
            self.log(f"Disconnected from {disconnected_device_name}")

    async def read(self):
        try:
            if self.client and self.client.is_connected:
                request_uuid = self.request_uuid_var.get()
                characteristic_uuid = self.characteristic_uuid_var.get()

                await self.client.write_gatt_char(request_uuid, bytearray("get", "utf-8"))
                await asyncio.sleep(1.0)

                value = await self.client.read_gatt_char(characteristic_uuid)

                decoded_value = value.decode('utf-8').strip()
                if not decoded_value:
                    self.log("No data received from ESP32")
                    return

                self.log(f"Raw received data: {decoded_value}")

                try:
                    data = json.loads(decoded_value)
                    self.log(f"Parsed JSON data: {json.dumps(data, indent=2)}")

                    cargo_id = data.get("CargoID", "N/A")
                    longitude = data.get("Longitude", "N/A")
                    latitude = data.get("Latitude", "N/A")
                    address = data.get("Address", "N/A")
                    full_name = data.get("FullName", "N/A")
                    price = data.get("Price", "N/A")
                    weight = data.get("Weight", "N/A")
                    description = data.get("Description", "N/A")

                    self.log(f"Processed data:")
                    self.log(f"CargoID: {cargo_id}")
                    self.log(f"Longitude: {longitude}")
                    self.log(f"Latitude: {latitude}")
                    self.log(f"Address: {address}")
                    self.log(f"Full Name: {full_name}")
                    self.log(f"Price: {price}")
                    self.log(f"Weight: {weight}")
                    self.log(f"Description: {description}")

                    self.cargo_id_var.set(cargo_id)
                    self.longitude_var.set(longitude)
                    self.latitude_var.set(latitude)
                    self.address_var.set(address)
                    self.full_name_var.set(full_name)
                    self.price_var.set(price)
                    self.weight_var.set(weight)
                    self.description_var.set(description)

                except json.JSONDecodeError as e:
                    self.log(f"Error decoding JSON: {str(e)}")
                    self.log(f"Received data: {decoded_value}")

        except Exception as e:
            self.status_label.config(text=f"Status: {str(e)}")
            self.log(f"Error in read: {str(e)}")

    async def write(self):
        try:
            error_flag = False
            if not self.client or not self.client.is_connected:
                self.log("Not connected to any device.")
                return

            cargo_id = self.cargo_id_var.get().strip()
            longitude = self.longitude_var.get().strip()
            latitude = self.latitude_var.get().strip()
            address = self.address_var.get().strip()
            full_name = self.full_name_var.get().strip()
            price = self.price_var.get().strip()
            weight = self.weight_var.get().strip()
            description = self.description_var.get().strip()

            # Валидация данных
            if not cargo_id.isdigit() or not cargo_id:
                self.log("Cargo ID must be numeric and not empty.")
                error_flag = True

            try:
                longitude = float(longitude)
                if not (-180 <= longitude <= 180):
                    raise ValueError("Longitude out of range.")
            except ValueError as e:
                self.log(f"Invalid Longitude: {e}")
                error_flag = True

            try:
                latitude = float(latitude)
                if not (-90 <= latitude <= 90):
                    raise ValueError("Latitude out of range.")
            except ValueError as e:
                self.log(f"Invalid Latitude: {e}")
                error_flag = True

            if not price or not description or not address or not full_name:
                self.log("Price, Description, Address and Full Name cannot be empty.")
                error_flag = True

            try:
                price = float(price)
            except ValueError:
                self.log("Price must be a valid number.")
                error_flag = True

            try:
                weight = float(weight)
            except ValueError:
                self.log("Weight must be a valid number.")
                error_flag = True

            if len(address) > 128:
                self.log("Address exceeds 128 characters.")
                error_flag = True

            if len(full_name) > 128:
                self.log("Full Name exceeds 128 characters.")
                error_flag = True

            if len(description) > 128:
                self.log("Description exceeds 128 characters.")
                error_flag = True

            if error_flag:
                return

               data = {
                "CargoID": cargo_id,
                "Longitude": str(longitude),
                "Latitude": str(latitude),
                "Address": address,
                "FullName": full_name,
                "Price": str(price),
                "Weight": str(weight),
                "Description": description
            }
            json_data = json.dumps(data)
            characteristic_uuid = self.characteristic_uuid_var.get()
            await self.client.write_gatt_char(characteristic_uuid, json_data.encode('utf-8'))
            self.log(f"Sent: {json_data}")
        except Exception as e:
            self.log(f"Error writing: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = BLEApp(root)
    async_mainloop(root)