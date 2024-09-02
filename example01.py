import math

import gym
import gym.spaces
import numpy as np
from stable_baselines3 import PPO


class MyEnv(gym.Env):
    def __init__(self):
        super().__init__()

        self.observation = None
        self.reward = None
        self.action = None
        self.done = False

        self.observation_space = gym.spaces.Box(-1.0, 1.0, shape=(5,))
        self.action_space = gym.spaces.Box(-1.0, 1.0, shape=(1,))
        self.reward_range = [-1.0, 1.0]

    def reset(self):
        initial_observation = np.array([0.0, 0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        return initial_observation

    def step(self, action):
        observation = np.array([0.0, 0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        reward = math.sin(action * math.pi) + np.random.normal(0, 0.1)
        done = np.random.uniform(0, 10) < 0.1

        self.observation = observation
        self.reward = reward
        self.action = action
        self.done = done

        return observation, reward, done, {}

    def render(self, mode="human", close=False):
        print(self.observation)
        print(self.reward)
        print(self.action)

    def close(self):
        pass

    def seed(self, seed=None):
        pass


def main():
    env = MyEnv()
    model = PPO("MlpPolicy", env, verbose=1)

    model.learn(total_timesteps=10000)

    state = env.reset()
    while True:
        env.render()
        action, _ = model.predict(state, deterministic=True)
        state, reward, done, info = env.step(action)
        if done:
            break
    env.close()


if __name__ == "__main__":
    main()
