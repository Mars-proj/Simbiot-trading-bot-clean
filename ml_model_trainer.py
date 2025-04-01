import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from logging_setup import logger_main
import os

class TradingModel(nn.Module):
    def __init__(self, input_size, hidden_size=64):
        super(TradingModel, self).__init__()
        self.layer1 = nn.Linear(input_size, hidden_size)
        self.relu1 = nn.ReLU()
        self.layer2 = nn.Linear(hidden_size, hidden_size // 2)
        self.relu2 = nn.ReLU()
        self.output = nn.Linear(hidden_size // 2, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.layer1(x)
        x = self.relu1(x)
        x = self.layer2(x)
        x = self.relu2(x)
        x = self.output(x)
        x = self.sigmoid(x)
        return x

def train_model(X_train, y_train, model_path, epochs=100, batch_size=32, learning_rate=0.001):
    """Trains a deep neural network for trading predictions."""
    try:
        # Convert data to torch tensors
        X_train = torch.FloatTensor(X_train)
        y_train = torch.FloatTensor(y_train).view(-1, 1)

        # Initialize model
        input_size = X_train.shape[1]
        model = TradingModel(input_size)
        criterion = nn.BCELoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)

        # Training loop
        model.train()
        for epoch in range(epochs):
            for i in range(0, len(X_train), batch_size):
                batch_X = X_train[i:i + batch_size]
                batch_y = y_train[i:i + batch_size]

                # Forward pass
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)

                # Backward pass and optimization
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            if (epoch + 1) % 10 == 0:
                logger_main.info(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")

        # Save the model
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        torch.save(model.state_dict(), model_path)
        logger_main.info(f"Model trained and saved to {model_path}")

        # Calculate training accuracy
        model.eval()
        with torch.no_grad():
            outputs = model(X_train)
            predictions = (outputs >= 0.5).float()
            accuracy = (predictions == y_train).float().mean().item()
            logger_main.info(f"Training accuracy: {accuracy:.4f}")

        return model, {'accuracy': accuracy, 'final_loss': loss.item()}
    except Exception as e:
        logger_main.error(f"Error training model: {e}")
        return None, None

__all__ = ['train_model']
