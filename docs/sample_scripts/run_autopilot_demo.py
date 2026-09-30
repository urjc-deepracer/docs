
import carla, time, pygame, numpy as np, cv2, torch, queue
from queue import Queue
from torchvision import transforms
from pilotnet import PilotNet
from PIL import Image

MODEL_PATH = "pilot_net_model_best_123.pth"
image_shape = (66, 200, 4)
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

model = PilotNet(image_shape, num_labels=2).to(device)
state = torch.load(MODEL_PATH, map_location=device)
model.load_state_dict(state)
model.eval()

transform = transforms.Compose([
    transforms.Resize((66, 200)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5]*3, std=[0.5]*3)
])

HOST, PORT = '127.0.0.1', 2000
VEHICLE_MODEL = 'vehicle.finaldeepracer.aws_deepracer'
WIDTH, HEIGHT = 800, 600
FPS = 30.0
FIXED_DT = 1.0 / FPS
WARMUP_SEC = 2.0  # time before passing to the network

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DeepRacer")

client = carla.Client(HOST, PORT)
client.set_timeout(5.0)
client.load_world('Circuits')
world = client.get_world()

weather = carla.WeatherParameters(
    cloudiness=80.0,
    precipitation=0.0,
    sun_altitude_angle=90.0,
    fog_density=0.0,
    wetness=0.0
)
world.set_weather(weather)
bp = world.get_blueprint_library()
vehicle_bp = bp.find(VEHICLE_MODEL)

# ------------------------- TRACK05 ---------------------------------
spawn_point = carla.Transform(
   carla.Location(x=-3.7, y=-4, z=0.5),
   carla.Rotation(yaw=-120)
)

vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
if not vehicle:
    print("Error spawning the vehicle")
    raise SystemExit
print("Vehicle spawned successfully")

# --- cameras ---

cam_bp_net = bp.find('sensor.camera.rgb')
cam_bp_net.set_attribute('image_size_x', str(WIDTH))
cam_bp_net.set_attribute('image_size_y', str(HEIGHT))
cam_bp_net.set_attribute('fov', '90')
cam_bp_net.set_attribute('sensor_tick', '0.0')

cam_bp_thirdperson = bp.find('sensor.camera.rgb')
cam_bp_thirdperson.set_attribute('image_size_x', str(WIDTH))
cam_bp_thirdperson.set_attribute('image_size_y', str(HEIGHT))
cam_bp_thirdperson.set_attribute('fov', '90')
cam_bp_thirdperson.set_attribute('sensor_tick', '0.0')

cam_tf = carla.Transform(carla.Location(x=0.13, z=0.13), carla.Rotation(pitch=-30))
cam_net = world.spawn_actor(cam_bp_net, cam_tf, attach_to=vehicle)

cam_tf_third = carla.Transform(
    carla.Location(x=-1.0, y=0.0, z=0.7),
    carla.Rotation(pitch=-12, yaw=0)  
)
cam_thirdperson = world.spawn_actor(cam_bp_thirdperson, cam_tf_third, attach_to=vehicle)

# frame buffers
rgb_net_q   = Queue(maxsize=1)    # 90 FOV for the network
rgb_third_q = Queue(maxsize=1)    # Third person

def _safe_put(q: Queue, item):
    try:
        q.put_nowait(item)
    except queue.Full:
        try: q.get_nowait()
        except queue.Empty: pass
        q.put_nowait(item)

def cb_third(image: carla.Image):
    bgra = np.frombuffer(image.raw_data, dtype=np.uint8).reshape(image.height, image.width, 4)
    _safe_put(rgb_third_q, bgra[:, :, :3][:, :, ::-1])

def cb_net(image: carla.Image):
    bgra = np.frombuffer(image.raw_data, dtype=np.uint8).reshape(image.height, image.width, 4)
    _safe_put(rgb_net_q, bgra[:, :, :3][:, :, ::-1])

cam_thirdperson.listen(cb_third)
cam_net.listen(cb_net)

vehicle.apply_control(carla.VehicleControl(throttle=0.0, steer=0.0))
time.sleep(1.0)

start_sim = world.get_snapshot().timestamp.elapsed_seconds
running = True

infer_tf = transforms.Compose([
            transforms.Resize((66, 200)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5]*3, std=[0.5]*3),
        ])

def draw_with_pip(main_rgb, pip_rgb):
    # main (third person) full size
    if main_rgb is not None:
        main_surf = pygame.surfarray.make_surface(main_rgb.swapaxes(0, 1))
        screen.blit(main_surf, (0, 0))

    # PiP (top right corner)
    if pip_rgb is not None:
        pip_w = WIDTH // 3
        pip_h = HEIGHT // 3
        pip_small = cv2.resize(pip_rgb, (pip_w, pip_h))
        pip_surf = pygame.surfarray.make_surface(pip_small.swapaxes(0, 1))
        screen.blit(pip_surf, (WIDTH - pip_w - 8, 8))

    pygame.display.flip()

clock = pygame.time.Clock()

while running:
    clock.tick(30) 
    
    snap = world.get_snapshot()
    if snap is None:
        continue
    sim_t = snap.timestamp.elapsed_seconds - start_sim
    dt    = snap.timestamp.delta_seconds
    
    # ESC to exit
    for e in pygame.event.get():
        if e.type == pygame.QUIT: running = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE: running = False

    # Get the last available frame (non-blocking)
    try: last_net   = rgb_net_q.get_nowait()
    except queue.Empty: pass
    try: last_third = rgb_third_q.get_nowait()
    except queue.Empty: pass

    # Inference with the 90° camera
    rgb_net = last_net

    if rgb_net is None:
        continue

    loc = vehicle.get_location()              # carla.Location
    cur_pos = np.array([loc.x, loc.y, loc.z], dtype=float)
    
    v = vehicle.get_velocity()
    speed = float(np.sqrt(v.x**2 + v.y**2 + v.z**2))
    print(speed)
 
    # Calculate speed (m/s) and scale it like in train (/3.5 and clip 0..1)
    speed_norm = float(np.clip(speed / 3.5, 0.0, 1.0))  # [0,1]

    # Generate HSV mask from captured RGB
    hsv = cv2.cvtColor(rgb_net, cv2.COLOR_RGB2HSV)

    lower_white  = np.array([0, 0, 200])
    upper_white  = np.array([180, 50, 255])

    lower_yellow = np.array([15, 70, 70])
    upper_yellow = np.array([35, 255, 255])

    mask_w = cv2.inRange(hsv, lower_white, upper_white)
    mask_y = cv2.inRange(hsv, lower_yellow, upper_yellow)

    mask = np.zeros_like(rgb_net)
    mask[mask_w > 0] = (255,255,255)   # class 1
    mask[mask_y > 0] = (255,255,0)     # class 2

    # Paint row 0–100 black
    mask[0:100, :, :] = 0 

    # Convert mask to tensor
    mask_img = Image.fromarray(mask)                    # PIL image
    x = infer_tf(mask_img).unsqueeze(0)                 # (1,3,66,200)

    # Speed channel
    speed_plane = torch.full((1,1,66,200), speed_norm,
                            dtype=x.dtype, device=x.device)

    x4 = torch.cat([x, speed_plane], dim=1).to(device)  # (1,4,66,200)

    with torch.no_grad():
        # pass tensor to model (reduces 4->3 with 1x1 adapter)
        out = model(x4)  
        steer, throttle = out[0].tolist()

    steer    = float(np.clip(steer,    -1.0, 1.0))
    throttle = float(np.clip(throttle,  0.0, 1.0))

    vehicle.apply_control(carla.VehicleControl(throttle=throttle, steer=steer))

    draw_with_pip(last_third, mask)

# cleanup
try: cam_net.stop(); cam_net.destroy()
except: pass
try: cam_third.stop(); cam_third.destroy()
except: pass

try: vehicle.destroy()
except: pass
pygame.quit()