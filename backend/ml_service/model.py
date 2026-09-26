"""BiLSTM architecture — must match the training notebook exactly."""

import torch.nn as nn


class BiLSTMModel(nn.Module):
    def __init__(self, n_channels=23, hidden=64, layers=2, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            n_channels,
            hidden,
            layers,
            batch_first=True,
            dropout=dropout,
            bidirectional=True,
        )
        self.dropout = nn.Dropout(dropout)
        # hidden * 2 because the LSTM is bidirectional
        self.fc = nn.Linear(hidden * 2, 2)

    def forward(self, x):          # x: (batch, 256, 23)
        out, _ = self.lstm(x)      # (batch, 256, hidden*2)
        out = out.mean(dim=1)      # average over time
        return self.fc(self.dropout(out))