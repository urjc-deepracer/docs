# Remote Control Deepracer

<video width="1280" height="720" controls>
  <source src="../images/Remote.mp4" type="video/mp4">
</video>

This guide explains how to use a PS4 Controller (Dualshock) connected to your local laptop to remotely control a vehicle in CARLA simulator running on a remote server. The connection between the joystick and CARLA is made through SSH and socket communication.

![1](images/ps4.jpeg)

It was made like this, so that we could use a much better PC and connect it through SSH to our laptop. However, it can be all done in the same PC at once by directly sending data to the Carla server.

Besides, any controller can be used, as long as you are able to get its data. This implementation was also tested in an Xbox Controller and Nintendo Switch Pro Controller and it worked as well. (Notice how each device sends messages in different ways with different intervals).

Make sure that you have installed evdev Python package:

```bash
pip install evdev
```

Make sure it works by typing:

```bash
sudo evtest
```

```bash
No device specified, trying to scan all of /dev/input/event*
Available devices:
/dev/input/event0:	Lid Switch
/dev/input/event1:	Sleep Button
/dev/input/event2:	Power Button
/dev/input/event3:	Power Button
/dev/input/event4:	AT Translated Set 2 keyboard
/dev/input/event5:	CUST0001:00 04F3:30AA Mouse
/dev/input/event6:	CUST0001:00 04F3:30AA Touchpad
/dev/input/event7:	ETPS/2 Elantech Touchpad
/dev/input/event8:	Corsair CORSAIR HARPOON RGB PRO Gaming Mouse
/dev/input/event9:	Corsair CORSAIR HARPOON RGB PRO Gaming Mouse
/dev/input/event10:	Corsair CORSAIR HARPOON RGB PRO Gaming Mouse
/dev/input/event11:	MSI WMI hotkeys
/dev/input/event12:	gpio-keys
/dev/input/event13:	Video Bus
/dev/input/event14:	Video Bus
/dev/input/event15:	HDA Intel PCH Mic
/dev/input/event16:	HDA Intel PCH Headphone
/dev/input/event17:	HDA Intel PCH HDMI/DP,pcm=3
/dev/input/event18:	HDA Intel PCH HDMI/DP,pcm=7
/dev/input/event19:	HDA Intel PCH HDMI/DP,pcm=8
/dev/input/event20:	Sony Interactive Entertainment Wireless Controller
/dev/input/event21:	Sony Interactive Entertainment Wireless Controller Motion Sensors
/dev/input/event22:	Sony Interactive Entertainment Wireless Controller Touchpad
Select the device event number [0-22]: 
```

In my case, I'm currently using a PS4 controller, and I only want to use its buttons — not the touchpad or sensors. As so, I'll be typing 20 and be able to watch the values changing from ranges 0-255 while moving the joysticks:

```bash
Event: time 1754051218.570172, -------------- SYN_REPORT ------------
Event: time 1754051218.574173, type 3 (EV_ABS), code 0 (ABS_X), value 65
Event: time 1754051218.574173, type 3 (EV_ABS), code 1 (ABS_Y), value 221
Event: time 1754051218.574173, type 3 (EV_ABS), code 3 (ABS_RX), value 87
Event: time 1754051218.574173, type 3 (EV_ABS), code 4 (ABS_RY), value 254
Event: time 1754051218.574173, -------------- SYN_REPORT ------------
Event: time 1754051218.578170, type 3 (EV_ABS), code 0 (ABS_X), value 55
Event: time 1754051218.578170, type 3 (EV_ABS), code 1 (ABS_Y), value 228
Event: time 1754051218.578170, type 3 (EV_ABS), code 3 (ABS_RX), value 81
Event: time 1754051218.578170, type 3 (EV_ABS), code 4 (ABS_RY), value 252
Event: time 1754051218.578170, -------------- SYN_REPORT ------------
Event: time 1754051218.582177, type 3 (EV_ABS), code 0 (ABS_X), value 46
Event: time 1754051218.582177, type 3 (EV_ABS), code 1 (ABS_Y), value 234
Event: time 1754051218.582177, type 3 (EV_ABS), code 3 (ABS_RX), value 75
Event: time 1754051218.582177, type 3 (EV_ABS), code 4 (ABS_RY), value 249
Event: time 1754051218.582177, -------------- SYN_REPORT ------------
Event: time 1754051218.586179, type 3 (EV_ABS), code 0 (ABS_X), value 39
Event: time 1754051218.586179, type 3 (EV_ABS), code 1 (ABS_Y), value 240
Event: time 1754051218.586179, type 3 (EV_ABS), code 3 (ABS_RX), value 69
Event: time 1754051218.586179, type 3 (EV_ABS), code 4 (ABS_RY), value 246
Event: time 1754051218.586179, -------------- SYN_REPORT ------------
Event: time 1754051218.590181, type 3 (EV_ABS), code 0 (ABS_X), value 34
Event: time 1754051218.590181, type 3 (EV_ABS), code 1 (ABS_Y), value 239
Event: time 1754051218.590181, type 3 (EV_ABS), code 3 (ABS_RX), value 62
Event: time 1754051218.590181, type 3 (EV_ABS), code 4 (ABS_RY), value 245
Event: time 1754051218.590181, -------------- SYN_REPORT ------------
```
If this worked for you, your device is connected.

To test its workability, as we are using sockets, we will have the joystick client code on our laptop and the carla receiver in the remote server.


### How to run it??

**Step 1**: Run Receiver on Remote Server:

```bash
python3 receiver_car_control.py
```

**Step 2**: SSH Port Forwarding (on local laptop)


Open one terminal and connect ssh to the remote server. Make sure that you are using an available port, avoid the commonly used ones. In my case I'll be using PORT 1977

```bash
ssh -p PORT user@host
```

If you are using an intermediate remote pc to reach the final destination:

```bash
ssh -J user@midhost user@finalhost -L PORT:localhost:PORT
```

Keep this terminal open.

**Step 3**: Run Joystick Client on Local Laptop

```bash
python3 joystick_client.py
```



## Joystick client

```python3
import socket
from evdev import InputDevice, categorize, ecodes, list_devices
import select

HOST = 'localhost'
PORT = 1977

# Search for device
devices = [InputDevice(path) for path in list_devices()]
joystick = None
for device in devices:
    if "Sony" in device.name or "Wireless Controller" in device.name or "PS4" in device.name:
        joystick = device
        break

if not joystick:
    print("No PS4 controller found")
    exit()

print(f"? Using device: {joystick.path} - {joystick.name}")

# Connect
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("? Connected to receiver")

    abs_x = 0
    abs_z = 0     # L2
    abs_rz = 0    # R2

    for event in joystick.read_loop():
        if event.type == ecodes.EV_ABS:
            if event.code == ecodes.ABS_X:      # Left joystick (steer)
                abs_x = event.value
            elif event.code == ecodes.ABS_Z:    # L2
                abs_z = event.value
            elif event.code == ecodes.ABS_RZ:   # R2
                abs_rz = event.value

            # Send values
            msg = f"[ABS_X] {abs_x}[R2] {abs_rz}[L2] {abs_z}\n"
            s.sendall(msg.encode())
```

## Receiver

This code simply allows you to check whether messages have been received or not:

```python3
import socket

HOST = 'localhost'
PORT = 1977

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Waiting for connection on {HOST}:{PORT}...")
    conn, addr = s.accept()
    with conn:
        print(f"Connected from {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode().strip()
            print(f"{msg}")
```

### What events does the joystick send when you move it?

When you move a game controller joystick (e.g., Nintendo Switch Pro Controller or PS4 DualShock) on Linux, the system sends axis events via the input system (like /dev/input/eventXX). These are the main axis events you receive:

**ABS_X:	Left joystick – Left/Right	From 0 to 255**

**R2:	Right Trigger – From From 0 to 255**

**L2:	Left Trigger – From From 0 to 255**

These values change dynamically as you move the sticks.

Example of raw messages from the joystick
If you print the raw values as they come in, you may see:

```bash
[ABS_X] 140[R2] 97[L2] 21
[ABS_X] 140[R2] 100[L2] 21
[ABS_X] 146[R2] 100[L2] 21
[ABS_X] 146[R2] 100[L2] 20
[ABS_X] 146[R2] 101[L2] 20
[ABS_X] 150[R2] 101[L2] 20
[ABS_X] 150[R2] 102[L2] 20
[ABS_X] 154[R2] 102[L2] 20
```

These messages show axis events where the numbers indicate how far and in what direction the joystick or thrigger has been moved.


Now we will use a manual control code to test this in a Carla world.

Execute the Unreal Engine package from the carla root folder:

```
CarlaUE4.sh
```
located at :

```
/Dist/CARLA_Shipping_0.9.15.2-2-gb23c01ae4-dirty/LinuxNoEditor
```
Now the server will be available to be connected to. Note that it can be launched with the flag ---RenderOffscreen to make it handier to use later.


Then for the client, you can use the same client code as before.
For the remote receiver, you have to create a python file (.py) so that the Deepracer behaves as the joystick is sending data.


```python3
import carla
import time
import pygame
import numpy as np
import socket

# Socket config
HOST = 'localhost'
PORT = 1977

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
print(f"Waiting for connection {HOST}:{PORT}...")
conn, addr = s.accept()
print(f"Connected from {addr}")

# Carla config
WIDTH, HEIGHT = 800, 600
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DeepRacer - Remote control")

client = carla.Client('127.0.0.1', 2000)
client.set_timeout(5.0)
world = client.get_world()

weather = carla.WeatherParameters(
    cloudiness=80.0,
    precipitation=0.0,
    sun_altitude_angle=90.0,
    fog_density=0.0,
    wetness=0.0
)
world.set_weather(weather)

blueprint_library = world.get_blueprint_library()
vehicle_bp = blueprint_library.find('vehicle.finaldeepracer.aws_deepracer')

spawn_point = carla.Transform(
    carla.Location(x=-7, y=-15, z=0.5),
    carla.Rotation(yaw=-15)
)

vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
if not vehicle:
    print("Unable to spawn vehicle")
    exit()
print("Vehicle spawned correctly")

camera_bp = blueprint_library.find('sensor.camera.rgb')
camera_bp.set_attribute('image_size_x', str(WIDTH))
camera_bp.set_attribute('image_size_y', str(HEIGHT))
camera_bp.set_attribute('fov', '90')
camera_transform = carla.Transform(carla.Location(x=-1, z=0.5))
camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)

camera_image = None
def process_image(image):
    global camera_image
    array = np.frombuffer(image.raw_data, dtype=np.uint8)
    array = np.reshape(array, (image.height, image.width, 4))[:, :, :3]
    array = array[:, :, ::-1]
    camera_image = pygame.surfarray.make_surface(array.swapaxes(0, 1))
camera.listen(process_image)

# Control vars
control = carla.VehicleControl()
current_steer = 0.0
current_throttle = 0.0
current_brake = 0.0

running = True
while running:
    try:
        buffer = conn.recv(1024).decode(errors='ignore').strip()
        if not buffer:
            continue

        lines = buffer.splitlines()
        for line in lines:
            if "[ABS_X]" in line and "[R2]" in line and "[L2]" in line:
                try:
                    parts = line.strip().split("[ABS_X]")
                    if len(parts) > 1:
                        vals = parts[1].split("[R2]")
                        if len(vals) == 2:
                            steer_val = int(vals[0].strip())
                            rest = vals[1].split("[L2]")
                            if len(rest) == 2:
                                r2_val = int(rest[0].strip())
                                l2_val = int(rest[1].strip())

                                # Escalar steer de 0-255 a -1 a 1
                                current_steer = (steer_val - 127) / 128.0
                                current_steer = max(-1.0, min(1.0, current_steer))

                                # Escalar R2 (aceleración) de 0-255 a 0.0-1.0
                                current_throttle = max(0.0, min(1, r2_val / 255.0))

                                # Escalar L2 (freno) de 255-0 a 0.001-0.1
                                brake_normalized = 1.0 - (l2_val / 255.0)
                                current_brake =  max(0.0, min(1.0, l2_val / 255.0))
                except Exception as e:
                    print("⚠️ Error parsing line:", e)
                    continue

        # Apply control
        control.steer = current_steer
        control.throttle = current_throttle
        control.brake = current_brake
        vehicle.apply_control(control)

        # Show camera
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if camera_image:
            screen.blit(camera_image, (0, 0))
        pygame.display.flip()

        # Speed display
        velocity = vehicle.get_velocity()
        speed = (velocity.x**2 + velocity.y**2 + velocity.z**2)**0.5
        print(f"Speed: {speed:.2f} m/s | Steer: {control.steer:.2f} | Throttle: {control.throttle:.2f} | Brake: {control.brake:.3f}")

    except KeyboardInterrupt:
        print("Interrupted")
        break

# Cleanup
camera.destroy()
vehicle.destroy()
pygame.quit()
conn.close()
s.close()
print("Session ended.")

```