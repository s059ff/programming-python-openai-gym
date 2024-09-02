import io
import json
import os
import socket
import subprocess
import time

import psutil


def launch_gameproc(*, training: bool = True):
    game_dir = "~/source/repos/programming-game-engine/ZephyrEngine/application02"
    game_dir = os.path.expanduser(game_dir)

    mode = "training" if training else "evaluation"
    args = [
        *["--mode", mode],
        *["--enemy_count", "1"],
        *["--friend_count", "0"],
        *["--random_seed", "8492"],
    ]

    proc = subprocess.Popen(
        [f"{game_dir}/bin/x64/Release/app.exe", *args],
        cwd=game_dir,
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


def main():
    if True:
        pid = launch_gameproc(training=True)
    else:
        app_name = "application02.exe"
        pids = [p.pid for p in psutil.process_iter() if p.name() == app_name]
        pid = pids[0]

    sock = connect(pid)

    while True:
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
        print(message)
        observation = json.loads(message)
        if observation["episode_done"]:
            continue

        response = {
            "roll_input": 0.5,
            "pitch_input": 0.5,
            "yaw_input": 0.0,
            "throttle_input": 0.5,
            "missile_launch_input": 0.0,
            "gun_fire_input": 0.0,
        }
        message = json.dumps(response)
        payload = message.encode("utf-8")
        sock.send(payload + bytes([0]))
        print(message)


if __name__ == "__main__":
    main()
