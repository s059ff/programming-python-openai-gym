import argparse
import os
import shutil
import sys
from datetime import datetime

from stable_baselines3 import PPO, SAC
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.logger import configure
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from environment import MyGameEnv


def make_env(runid: str, envid: int, *, debug: bool):
    # return lambda: MyGameEnv(env_index)

    # To write rollout/... to log, we need to use `Monitor`
    return lambda: Monitor(MyGameEnv(runid, envid, debug=debug))


def make_logger(log_dir: str):
    import logging

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(os.path.join(log_dir, "training.log"))
    formatter = logging.Formatter("%(levelname)s  %(asctime)s  [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", default="ppo", choices=["ppo", "sac"])
    parser.add_argument("-p", "--model_path", type=str)
    parser.add_argument("-i", "--runid", type=str)
    parser.add_argument("-n", "--num_envs", type=int, default=1)
    parser.add_argument("--gamma", type=float, default=0.995)
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    if args.debug:
        default_runid = f"{args.model}-debug"
    else:
        default_runid = datetime.now().strftime(f"{args.model}-%Y%m%d%H%M%S")

    args.runid = args.runid or default_runid

    return args


def main():
    args = parse_args()
    assert (args.model_path is None) or os.path.exists(args.model_path)

    log_dir = os.path.join("./logs", args.runid)
    shutil.rmtree(log_dir, ignore_errors=True)
    os.makedirs(log_dir, exist_ok=True)

    model_dir = os.path.join("./models", args.runid)
    shutil.rmtree(model_dir, ignore_errors=True)
    os.makedirs(model_dir, exist_ok=True)

    logger = make_logger(log_dir)
    logger.info(f"args: {args}")

    env = DummyVecEnv(
        [
            make_env(args.runid, envid, debug=args.debug)
            for envid in range(args.num_envs)
        ]
    )

    ModelType = {"ppo": PPO, "sac": SAC}[args.model]
    model: BaseAlgorithm = ModelType(
        "MlpPolicy", env, verbose=1, device=args.device, gamma=args.gamma
    )
    print(model.policy)

    if args.model_path:
        model.load(args.model_path)

    mylogger = configure(log_dir, ["log", "csv", "tensorboard"])
    model.set_logger(mylogger)

    checkpoint_callback = CheckpointCallback(
        save_freq=100000,
        save_path=model_dir,
        save_replay_buffer=True,
    )

    try:
        model.learn(total_timesteps=sys.maxsize, callback=checkpoint_callback)
    finally:
        model.save(f"{model_dir}/rl_model.zip")


if __name__ == "__main__":
    main()
