"""Classifier from pinned notebook cell 28."""

import torch
from torch import nn


class WakewordModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.layer1 = nn.Linear(16 * 96, 128)
        self.layernorm1 = nn.LayerNorm(128)
        self.relu1 = nn.ReLU()
        self.layer2 = nn.Linear(128, 1)

    def forward(self, x):
        return self.layer2(self.relu1(self.layernorm1(self.layer1(self.flatten(x)))))


class ProbabilityModel(nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, x):
        return torch.sigmoid(self.model(x))
