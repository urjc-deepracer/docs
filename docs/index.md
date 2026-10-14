# Deepracer Carla Simulator wiki

![1](images/dr.jpg)

**Welcome to the wiki!**

Here you will find step by step how to import and work with the AWS Deepracer in Carla Simulator (0.9.15 version).

# Quick Start:

# 1. Clone sample project
```bash
git clone https://github.com/urjc-deepracer/carla-deepracer-quickstart.git

cd carla-deepracer-quickstart
```

# 2 Create and activate virtual environment

```bash
python3 -m venv deepracer_carla
source deepracer_carla/bin/activate
```

### 2.2 Install dependencies
```bash
pip install -r requirements.txt
```

### 2.3 Download weight binary file

```bash
wget -O pilot_net_model_best_123.pth "https://github.com/urjc-deepracer/sim-carla-il-deepracer/releases/download/1.0.0/pilot_net_model_best_123.pth"
```


# 3. Download & Extract CARLA Simulator

```bash
chmod +x install_carla.sh
./install_carla.sh
```
*Note: (You can also manually d ownload the pre-compiled CARLA package (v0.9.15) from [this Google Drive link](https://drive.google.com/file/d/1J0SOiZaXrFiA-FcyDWagMZQWEipHdKY9/view?usp=sharing) by yourself)*



# 4. Launch the Simulator

Navigate to where the pre-compiled CARLA package was extracted, then navigate to:

```bash
  cd ./carla_server
```
Launch the simulator: (Render off screen flag is used so that the window does not pop up)

```bash
  ./CarlaUE4.sh -RenderOffScreen
```

# 5. Client Script Examples

Open a **new terminal** window, navigate to the repository, and activate your virtual environment:

```bash
cd carla-deepracer-quickstart
source deepracer_carla/bin/activate
```

*Note: Make sure your virtual environment is activated (source deepracer_carla/bin/activate) before running any script.*

## Manual control

```bash
  python3 deepracer_manual_control.py --cam 4
```

- --cam: Select top-down camera track view (Available: 1-5 and 8-13).

You will be able to drive the car using the W,A,S keys:
- W: throttle 
- A: left steering
- D: right steering

## Imitation learning

Test the Deepracer driving by itself!

```bash
python3 videocam.py --mode trail --cam 4
```

- --mode: Select visualization mode (trail for trajectory line or heatmap).

- --cam: Select top-down camera track view (Available: 1-5 and 8-13).

press 'q'  to exit all windows


--- 

---

In case you want to explore or modify any process part or asset, here is the full guide with the links to the different tutorials. They explain the creation an implementation of the Deepracer and the creation and implementation of the Racetracks.

- [Each individual part documentation links](secondindx.md)

