import torch
import torch.nn as nn

class Agent(nn.Module):
    def __init__(self):
        super(Agent, self).__init__()

    def get_action(self, state:object):
        pass

    def save_xp(self, trajectory:tuple):
        pass

    def train(self):
        pass

    def save_model(self, save_dir:str):
        pass

    def load_model(self, load_dir:str):
        pass