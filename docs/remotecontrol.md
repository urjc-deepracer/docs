# Remote Control Deepracer

This guide explains how to use a Nintendo Switch Pro Controller connected to your local laptop to remotely control a vehicle in CARLA simulator running on a remote server. The connection between the joystick and CARLA is made through SSH and socket communication.

![1](images/nintendopro.jpeg)

It was made like this, so that we could use a much better PC and connect it through SSH to our laptop. However, it can be all done in the same PC at once.

Make sure that you have installed evdev Python package:

```bash
pip install evdev
```

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
import asyncio
from evdev import InputDevice, list_devices, ecodes
import socket

def find_joystick():
    devices = [InputDevice(path) for path in list_devices()]
    for device in devices:
        if 'Pro Controller' in device.name or 'Gamepad' in device.name or 'Joystick' in device.name:
            print(f"? Mando detectado: {device.name} en {device.path}")
            return device
    print("Unable to find controller")
    return None

async def main():
    device = find_joystick()
    if not device:
        return

    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 1977))
    print("Connected!")

    async for event in device.async_read_loop():
        if event.type == ecodes.EV_KEY:
            name = ecodes.KEY[event.code]
            value = 'pressed' if event.value else 'released'
            msg = f"[BTN] {name} {value}"
            print(msg)
            sock.sendall((msg + '\n').encode())

        elif event.type == ecodes.EV_ABS:
            axis = ecodes.ABS[event.code]
            msg = f"[AXIS] {axis} {event.value}"
            print(msg)
            sock.sendall((msg + '\n').encode())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n? Finalize")
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
    print(f"Waiting connection {HOST}:{PORT}...")
    conn, addr = s.accept()
    with conn:
        print(f"Connected from {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"Received data: {data.decode().strip()}")

```

### What events does the joystick send when you move it?

When you move a game controller joystick (e.g., Nintendo Switch Pro Controller or PS4 DualShock) on Linux, the system sends axis events via the input system (like /dev/input/eventXX). These are the main axis events you receive:

Common Axis Events from a Joystick
Axis Name	Represents Movement of...	Value Range
ABS_X	Left joystick – Left/Right	From -32768 to 32767
ABS_Y	Left joystick – Up/Down	From -32768 to 32767
ABS_RX	Right joystick – Left/Right	From -32768 to 32767
ABS_RY	Right joystick – Up/Down	From -32768 to 32767

These values change dynamically as you move the sticks.

Example of raw messages from the joystick
If you print the raw values as they come in, you may see:

```csharp
Copy code
[AXIS] ABS_X -428
[AXIS] ABS_Y 1054
[AXIS] ABS_RX 32767
[AXIS] ABS_RY -12983
```

These messages show axis events where the numbers indicate how far and in what direction the joystick has been moved.

Interpreting the values

ABS_X < 0 → Left joystick pushed left

ABS_X > 0 → Left joystick pushed right

ABS_Y < 0 → Left joystick pushed up

ABS_Y > 0 → Left joystick pushed down

(And similarly for ABS_RX, ABS_RY — just with the right joystick)


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


Then for the client, you have to create a python file (.py) so that the Deepracer behaves as the joystick is sending data.


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
client.load_world('Town01')

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

spawn_point = carla.Transform(carla.Location(x=2.95, y=-3.7, z=0.6), carla.Rotation(yaw=-90))
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


# Scale from joystick values [-32768, 32767] to [-1.0, 1.0]
def scale_axis(value, axis_type):

    if axis_type in ('ABS_X', 'ABS_RX'):
        return max(-1.0, min(1.0, value / 32767.0))
    elif axis_type in ('ABS_Y', 'ABS_RY'):
        return max(-1.0, min(1.0, value / 32767.0))
    return 0.0

control = carla.VehicleControl()
current_steer = 0.0
current_throttle = 0.0

running = True
while running:
    try:
        buffer = conn.recv(1024).decode(errors='ignore').strip()
        if not buffer:
            continue

        lines = buffer.splitlines()
        for line in lines:
            if "[AXIS]" not in line:
                continue
            if "ABS_X" in line:
                try:
                    val = int(line.split("ABS_X")[1].strip())
                    current_steer = scale_axis(val, 'ABS_X')
                except:
                    continue
            elif "ABS_Y" in line:
                try:
                    val = int(line.split("ABS_Y")[1].strip())
                    scaled = scale_axis(val, 'ABS_Y')
                    current_throttle = 0.6 * (1.0 - scaled) if scaled < 0 else 0.6 * (1.0 - abs(scaled))
                except:
                    continue

        # Apply control
        control.steer = current_steer
        control.throttle = max(0.0, current_throttle)
        control.brake = 0.0
        vehicle.apply_control(control)

        # Show camera
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if camera_image:
            screen.blit(camera_image, (0, 0))
        pygame.display.flip()

        # Speed
        velocity = vehicle.get_velocity()
        speed = (velocity.x**2 + velocity.y**2 + velocity.z**2)**0.5
        print(f"Speed: {speed:.2f} m/s  | Steer: {control.steer:.2f} | Throttle: {control.throttle:.2f}")

    except KeyboardInterrupt:
        print("Interrupted")
        running = False
        break

camera.destroy()
vehicle.destroy()
pygame.quit()
conn.close()
s.close()

```