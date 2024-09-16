import argparse

from stable_baselines3 import PPO, SAC

from environment import MyGameEnv


def make_env(env_id: int):
    return lambda: MyGameEnv(env_id)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", default="ppo", choices=["ppo", "sac"])
    parser.add_argument("-p", "--model_path", default="./models/ppo-latest.zip")
    parser.add_argument("-d", "--deterministic", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    runid = f"{args.model}-evaluation"
    envid = 0
    env = MyGameEnv(runid, envid, training=False, debug=False)

    ModelType = {"ppo": PPO, "sac": SAC}[args.model]
    model = ModelType.load(args.model_path, env)

    obs, info = env.reset()

    while True:
        action, state = model.predict(obs, deterministic=args.deterministic)
        obs, reward, done, truncated, info = env.step(action)
        if done:
            env.reset()
            continue


if __name__ == "__main__":
    main()
