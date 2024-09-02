import io
import json
import logging
import os
import socket
import subprocess
import time
from typing import Any, cast

import gymnasium
import gymnasium.spaces
import psutil


def launch_gameproc(runid: str, envid: int, *, training: bool = True):
    game_dir = "~/source/repos/programming-game-engine/ZephyrEngine/application02"
    game_dir = os.path.expanduser(game_dir)

    mode = "training" if training else "evaluation"
    args = [
        *["--mode", mode],
        *["--enemy_count", "1"],
        *["--friend_count", "0"],
        *["--random_seed", "8492"],
    ]
    logging.info(f"gameproc args: {args}")

    os.makedirs(f"./logs/{runid}/", exist_ok=True)

    proc = subprocess.Popen(
        [f"{game_dir}/bin/x64/Release/app.exe", *args],
        cwd=game_dir,
        stdout=open(f"./logs/{runid}/env{envid}-stdout.log", mode="w"),
        stderr=open(f"./logs/{runid}/env{envid}-stderr.log", mode="w"),
    )
    return proc.pid


def connect(pid: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = "127.0.0.1"
    port = 12345 + pid

    max_retries = 10
    for i in range(max_retries):
        try:
            print(f"Trying to connect to {address}:{port} ...")
            sock.connect((address, port))
        except BaseException:
            if i + 1 == max_retries:
                raise
            else:
                time.sleep(0.1)
        else:
            break

    return sock


def receive(sock: socket.socket):
    with io.BytesIO() as buffer:
        while True:
            chunk = sock.recv(4096)
            if chunk == b"":
                raise RuntimeError("socket connection broken")
            buffer.write(chunk)
            if chunk[-1] == 0:
                break
        buffer.seek(0)
        payload = buffer.getvalue()
        assert 0 < len(payload)
        assert payload[-1] == 0

    message = payload[:-1].decode("utf-8")
    obj = json.loads(message)
    return cast(dict[str, Any], obj)


def observe(obj: dict[str, Any]):
    array = [
        obj["player"]["armor_delta"],  # 1
        *obj["player"]["position"],  # 3
        *obj["player"]["rotation"],  # 4
        *obj["player"]["velocity"],  # 3
        obj["target"]["armor_delta"],  # 1
        *obj["target"]["position"],  # 3
        *obj["target"]["rotation"],  # 4
        *obj["target"]["velocity"],  # 3
        *obj["threat_missile"]["position"],  # 3
        *obj["threat_missile"]["rotation"],  # 4
        *obj["threat_missile"]["velocity"],  # 3
    ]
    return array


def send(sock: socket.socket, obj: dict[str, Any]):
    message = json.dumps(obj)
    payload = message.encode("utf-8")
    sock.send(payload)
    sock.send(bytes([0]))


def act(action: gymnasium.spaces.Space):
    obj = {
        "roll_input": float(action[0]),
        "pitch_input": float(action[1]),
        "yaw_input": float(action[2]),
        "throttle_input": float(action[3]),
        "missile_launch_input": float(action[4]),
        "gun_fire_input": float(action[5]),
    }
    return cast(dict[str, Any], obj)


class MyGameEnv(gymnasium.Env):
    D = 2 + 10 + 10 + 10
    A = 6

    def __init__(
        self,
        runid: str,
        envid: int,
        *,
        training: bool = True,
        debug: bool = False,
    ):
        super().__init__()

        self.runid = runid
        self.envid = envid
        if debug:
            app_name = "app.exe"
            self.pid = [p.pid for p in psutil.process_iter() if p.name() == app_name][0]
        else:
            self.pid = launch_gameproc(runid, envid, training=training)

        self.training = training
        self.sock = connect(self.pid)
        logging.debug(f"runid: {self.runid}")
        logging.debug(f"envid: {self.envid}")
        logging.debug(f"pid: {self.pid}")
        logging.debug(f"training: {self.training}")

        self.observation_space = gymnasium.spaces.Box(-1.0, 1.0, shape=(MyGameEnv.D,))
        self.action_space = gymnasium.spaces.Box(-1.0, 1.0, shape=(MyGameEnv.A,))
        self.reward_range = [-1.0, 1.0]

    def reset(self, seed=None):
        # if self.sock:
        #     self.sock.close()
        # self.sock = connect(self.pid)
        obs = observe(receive(self.sock))
        info = {}
        return obs, info

    def step(self, action):
        send(self.sock, act(action))

        obj = receive(self.sock)
        obs = observe(obj)

        rew = 0.0
        rew += obj["player"]["armor_delta"]
        rew += -obj["target"]["armor_delta"]

        done = obj["episode_done"]

        truncated = False

        info = {}

        return obs, rew, done, truncated, info

    def render(self, mode="human", close=False):
        pass

    def close(self):
        self.sock.close()
        self.sock = None

        proc = psutil.Process(self.pid)
        proc.terminate()
        self.pid = None

    def seed(self, seed=None):
        pass
