# Carla client

## Index:

- [Connection with server](#Connection-with-server)
- [Deepracer Camera settings](#Deepracer-camera-settings)
- [Client time vs real time](#Client-time-vs-real-time)
- [HSV Filter and mask segmentation](#HSV-Filter-and-mask-segmentation)
- [Generate Dataset](#Generate-dataset)

---

<video width="1280" height="720" controls>
  <source src="../images/manualcontrol.webp" type="video/webm">
</video>
(Map modified as the ramp has been added)

## Connection with server

Once the package is compressed at the carla root folder:

```bash
make package
```
Execute 
```
CarlaUE4.sh
```
located at :

```
/Dist/CARLA_Shipping_0.9.15.2-2-gb23c01ae4-dirty/LinuxNoEditor
```
Now the server will be available to be connected to. Note that it can be launched with the flag ---RenderOffscreen to make it handier to use later.


Then for the client, you have to create a python file (.py). 

We are going to use manualcontrol.py as an example, that will allow us to control the deepracer in the world we have just spawned. We will be using the keys W A S D as input:
-      w: Move forward
-      A: Turn left
-      S: Brake
-      D: Turn right


First, you must import the required modules:

```python
import carla
import time
import pygame
import numpy as np
```
- carla: CARLA client API

- time: for sleep/wait operations

- pygame: for keyboard input and display

- numpy: to process camera image data


Configuration for the CARLA server and the vehicle blueprint.


```python
HOST = '127.0.0.1'
PORT = 2000
VEHICLE_MODEL = 'vehicle.finaldeepracer.aws_deepracer'
```

Initialize Pygame for displaying the RGB camera feed.

```python
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DeepRacer")

```
Connect to CARLA, set timeout, and load a specific map (Town01).


```python
client = carla.Client(HOST, PORT)
client.set_timeout(5.0)
world = client.get_world()
client.load_world('Town01') 

```
Set sunny weather with clouds but no rain or fog.

```python
weather = carla.WeatherParameters(
    cloudiness=80.0,
    precipitation=0.0,
    sun_altitude_angle=90.0,
    fog_density=0.0,
    wetness=0.0
)
world.set_weather(weather)
```

Spawn the DeepRacer Vehicle. Get the blueprint for the AWS DeepRacer vehicle.

```python
blueprint_library = world.get_blueprint_library()
vehicle_bp = blueprint_library.find(VEHICLE_MODEL)
```
Set vehicle spawn location and attempt to spawn it. If it fails, the program exits.

```python
spawn_point = carla.Transform(carla.Location(x=2.95, y=-3.7, z=0.6),
                carla.Rotation(pitch=0, yaw=-90, roll=0))
vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
```

Attach an RGB Camera to the Vehicle.Configure the RGB camera sensor with resolution and field of view.


```python
camera_rgb_bp = blueprint_library.find('sensor.camera.rgb')
camera_rgb_bp.set_attribute('image_size_x', str(WIDTH))
camera_rgb_bp.set_attribute('image_size_y', str(HEIGHT))
camera_rgb_bp.set_attribute('fov', '90')
```
Place and attach the camera to the vehicle.

```python
camera_rgb_transform = carla.Transform(carla.Location(x=-1, z=0.5))
camera_rgb = world.spawn_actor(camera_rgb_bp, camera_rgb_transform, attach_to=vehicle)
```

Process RGB Image from Camera.
Convert raw image data into a Pygame surface for display.

```python
def process_rgb(image):
    global camera_image_rgb
    array = np.frombuffer(image.raw_data, dtype=np.uint8)
    array = np.reshape(array, (image.height, image.width, 4))[:, :, :3]
    array = array[:, :, ::-1]
    camera_image_rgb = pygame.surfarray.make_surface(array.swapaxes(0, 1))
```

Start listening to camera stream and process frames in real time:

```python
camera_rgb.listen(lambda image: process_rgb(image))

```

Start the control loop and poll the keyboard.

```python
control = carla.VehicleControl()
running = True

while running:
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]: ...
    if keys[pygame.K_a]: ...
    if keys[pygame.K_d]: ...
    if keys[pygame.K_s]: ...
    control.hand_brake = keys[pygame.K_SPACE]
```
Apply control values to the vehicle.

```python
vehicle.apply_control(control)
```

Event Handling and Display

```python
for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    
    if camera_image_rgb:
        screen.blit(camera_image_rgb, (0, 0))

    pygame.display.flip()
```

--- 

Here is the **FULL CODE**: 

```python
import carla
import time
import pygame
import numpy as np

HOST = '127.0.0.1'
PORT = 2000
VEHICLE_MODEL = 'vehicle.finaldeepracer.aws_deepracer'

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DeepRacer")


client = carla.Client(HOST, PORT)
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
vehicle_bp = blueprint_library.find(VEHICLE_MODEL)


spawn_point = carla.Transform(carla.Location(x=2.95, y=-3.7, z=0.6),
                carla.Rotation(pitch=0, yaw=-90, roll=0))

vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
if not vehicle:
    print("unable to spanw")
    exit()
print(f"vehicle {VEHICLE_MODEL} spaned at {spawn_point.location}")

camera_rgb_bp = blueprint_library.find('sensor.camera.rgb')
camera_rgb_bp.set_attribute('image_size_x', str(WIDTH))
camera_rgb_bp.set_attribute('image_size_y', str(HEIGHT))
camera_rgb_bp.set_attribute('fov', '90')


camera_rgb_transform = carla.Transform(carla.Location(x=-1, z=0.5))
camera_rgb = world.spawn_actor(camera_rgb_bp, camera_rgb_transform, attach_to=vehicle)


camera_image_rgb = None


def process_rgb(image):
    global camera_image_rgb
    array = np.frombuffer(image.raw_data, dtype=np.uint8)
    array = np.reshape(array, (image.height, image.width, 4))[:, :, :3]
    array = array[:, :, ::-1]
    camera_image_rgb = pygame.surfarray.make_surface(array.swapaxes(0, 1))



camera_rgb.listen(lambda image: process_rgb(image))

control = carla.VehicleControl()
running = True

while running:
    keys = pygame.key.get_pressed()

    if keys[pygame.K_w]:
        control.throttle = min(control.throttle + 0.01, 0.8)

    else:
        control.throttle = 0.0

        
    control.brake = min(control.brake + 0.1, 1.0) if keys[pygame.K_s] else 0.0

    if keys[pygame.K_a]:
        control.steer = max(control.steer - 0.05, -1.0)

    elif keys[pygame.K_d]:
        control.steer = min(control.steer + 0.05, 1.0)

    else:
        control.steer = 0.0

    control.hand_brake = keys[pygame.K_SPACE]

    vehicle.apply_control(control)

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    
    if camera_image_rgb:
        screen.blit(camera_image_rgb, (0, 0))

    pygame.display.flip()
    

camera_rgb.destroy()
vehicle.destroy()
pygame.quit()

```

Now execute the code:

```bash
python3 manualcontrol.py
```

---

## Deepracer Camera Settings


To replicate the same camera settings as the actual Deepracer (using the front POV camera). We will need these settings. They represent the location of the camera and its pitch, as it is a bit tilted and facing down.

```python
camera_rgb_bp = blueprint_library.find('sensor.camera.rgb')
camera_rgb_bp.set_attribute('image_size_x', str(WIDTH))
camera_rgb_bp.set_attribute('image_size_y', str(HEIGHT))
camera_rgb_bp.set_attribute('fov', '120')


transform_front = carla.Transform(carla.Location(x=0.13, z=0.13), carla.Rotation(pitch=-30))
camera_front = world.spawn_actor(camera_rgb_bp, transform_front, attach_to=vehicle)
```

## Client time vs real time

Always run the simulator at fixed time-step when using the synchronous mode. 

Otherwise the physics engine will try to recompute at once all the time spentwaiting for the client, this usually results in inconsistent or not very realistic physics.

Fixed time-step The simulation runs as fast as possible, 
simulating the same time increment on each step. To enable this mode set a fixed delta seconds in the world settings.

We want to prove that there is a difference between the time it takes for the computer to iterate, and the time it takes for the client to perform the callback function.


We are going to set 20 FPS as an example for the callback.

We will be using a callback function named: camera_callback(). And in our while loop, we will print
```
while running:

    # Move on to the next iteration with world.tick()
    t1 = time.time()
    world.tick()
    t2 = time.time()
    print(f"real time gap: {t2-t1}")
```
every time it iterates. 
 
We will write another print inside the callback. Just to check every time that callback is actually performing:

```
def camera_callback(image):
    print(f"[Frame {image.frame}] timestamp: {image.timestamp:.5f}")
```

We get this output:

```bash
real time gap: 0.0028502941131591797
real time gap: 0.0028717517852783203
[Frame 11578] timestamp: 162.86267
real time gap: 0.002864837646484375
[Frame 11579] timestamp: 162.91267
[Frame 11580] timestamp: 162.96267
real time gap: 0.0028464794158935547
[Frame 11581] timestamp: 163.01267
real time gap: 0.002921581268310547
real time gap: 0.0028870105743408203
[Frame 11582] timestamp: 163.06267
[Frame 11583] timestamp: 163.11267
real time gap: 0.0028617382049560547
[Frame 11584] timestamp: 163.16267
real time gap: 0.0031239986419677734
real time gap: 0.0028901100158691406
[Frame 11585] timestamp: 163.21267
[Frame 11586] timestamp: 163.26267
real time gap: 0.0029799938201904297

```

It means that our computer is taking aproximately 0.0028 seconds to perform the 'tick()' and move on to the next iteration. However, the callback can be seen that is ptinted every 0.05 seconds, which means it is performing at those 20 FPS (1/20).


Here is the code to try this out: 

```python3
import carla
import time
import pygame
import numpy as np
import matplotlib.pyplot as plt

HOST = '127.0.0.1'
PORT = 2000
VEHICLE_MODEL = 'vehicle.finaldeepracer.aws_deepracer'


pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DeepRacer - RGB y Segmentación Semántica")


client = carla.Client(HOST, PORT)
client.set_timeout(5.0)
world = client.get_world()

#FPS
settings = world.get_settings()
settings.synchronous_mode = True
settings.fixed_delta_seconds = 1.0 / 20.0
world.apply_settings(settings)

weather = carla.WeatherParameters(
    cloudiness=80.0,
    precipitation=0.0,
    sun_altitude_angle=90.0,
    fog_density=0.0,
    wetness=0.0
)
world.set_weather(weather)

blueprint_library = world.get_blueprint_library()
vehicle_bp = blueprint_library.find(VEHICLE_MODEL)


spawn_point = carla.Transform(
    carla.Location(x=3, y=-1, z=0.5),
    carla.Rotation(yaw=-90)
)
vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
if not vehicle:
    print("Error spawning")
    exit()


camera_rgb_bp = blueprint_library.find('sensor.camera.rgb')
camera_rgb_bp.set_attribute('image_size_x', str(WIDTH))
camera_rgb_bp.set_attribute('image_size_y', str(HEIGHT))
camera_rgb_bp.set_attribute('fov', '120')


transform_front = carla.Transform(carla.Location(x=0.13, z=0.13), carla.Rotation(pitch=-30))
transform_thirdpers = carla.Transform(carla.Location(x=-1, z=0.75))
camera_front = world.spawn_actor(camera_rgb_bp, transform_front, attach_to=vehicle)


def camera_callback(image):
    print(f"[Frame {image.frame}] timestamp: {image.timestamp:.5f}")



camera_front.listen(camera_callback)


control = carla.VehicleControl()
running = True

while running:

    # Move on to the next iteration with world.tick()
    t1 = time.time()
    world.tick()
    t2 = time.time()
    print(f"real time gap: {t2-t1}")


camera_rgb.destroy()
vehicle.destroy()
pygame.quit()
```


