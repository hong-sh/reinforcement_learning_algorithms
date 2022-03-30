from re import A
import supersuit
import pettingzoo.mpe.simple_tag_v2 as simple_tag_v2
import gym
import random
import numpy as np
from time import time
from tensorboardX import SummaryWriter

from agent.ppo_agent import PPOAgent

def get_action():
    return np.random.randint(0,5)

env_config = {
    "num_good" : 2,
    "num_adversaries" : 3,
    "num_obstacles" : 2,
    "max_cycles" : 50,
    "continuous_actions" : False
}

time_str = str(time())
log_dir = 'logs/mpe_main_' + time_str
model_dir = 'save_model/mpe_main_' + time_str


if __name__ == "__main__":
    env = simple_tag_v2.env(num_good=env_config["num_good"], num_adversaries=env_config["num_adversaries"], \
        num_obstacles=env_config["num_obstacles"], max_cycles=env_config["max_cycles"], \
            continuous_actions=env_config["continuous_actions"])
    
    # env = supersuit.normalize_obs_v0(env, env_min=-1, env_max=1)
    # env = supersuit.clip_reward_v0(env, lower_bound=-1, upper_bound=1)

    sum_of_agents = env_config["num_good"] + env_config["num_adversaries"]
    adversary_observation = 4 + (env_config["num_obstacles"] * 2) + (env_config["num_good"] + env_config["num_adversaries"]-1) * 2 + env_config["num_good"] * 2
    good_observation = 4 + (env_config["num_obstacles"] * 2) + (env_config["num_good"] + env_config["num_adversaries"]-1) * 2 + (env_config["num_good"]-1) * 2

    adversary_agent = PPOAgent(20 , 5, env_config["num_adversaries"])
    good_agent = PPOAgent(good_observation, 5)

    summary_writer = SummaryWriter(log_dir)

    for i_eps in range(10000):
        env.reset()
        prev_state = [np.zeros(20) for _ in range(env_config["num_adversaries"])]
        step_cnt = 0
        sum_reward = 0

        while step_cnt < env_config["max_cycles"] * sum_of_agents:
            agent_idx = step_cnt % sum_of_agents
            next_state, reward, done, info = env.last()
            next_state = np.clip(next_state, -10, 10) / 10
            # next_state = np.append(next_state[4:8], next_state[12:])
            reward = np.clip(reward, -10, 10) / 10
            if not done:
                # print('step cnt : {}'.format(step_cnt))
                action = 0
                if agent_idx < env_config["num_adversaries"]: 
                    action, action_prob = adversary_agent.get_action(next_state)
                    # print('agent_idx : {}, prev_state : {}'.format(agent_idx, prev_state[agent_idx]))
                    # print('action : {}, next_state : {}, reward : {}, done : {}, info : {}'.format(action, next_state, reward, done, info))
                    adversary_agent.save_xps(agent_idx, (prev_state[agent_idx], next_state, action, action_prob[action].item(), reward, done))
                    prev_state[agent_idx] = next_state
                    sum_reward += reward
                elif agent_idx >= env_config["num_adversaries"]:
                    action = get_action()

                env.step(action)
                # env.render()
            step_cnt += 1
        loss, pi_loss, value_loss, td_error =  adversary_agent.train()
        summary_writer.add_scalar('Loss/total_loss', loss, i_eps)
        summary_writer.add_scalar('Loss/pi_loss', pi_loss, i_eps)
        summary_writer.add_scalar('Loss/value_loss', value_loss, i_eps)
        summary_writer.add_scalar('Loss/td_error', td_error, i_eps)
        summary_writer.add_scalar('Episode reward', sum_reward, i_eps)
        print('{} eps total reward : {}'.format(i_eps, sum_reward))

        if i_eps % 100 == 0:
            adversary_agent.save_model(model_dir + '_eps_' + str(i_eps))
            