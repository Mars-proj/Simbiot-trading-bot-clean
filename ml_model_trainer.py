import torch
import torch.nn as nn
import torch.optim as optim
from logging_setup import logger_main
import os
import json

class SimpleNN(nn.Module):
    def __init__(self, input_size, hidden_size=64):
        super(SimpleNN, self).__init__()
        self.layer1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.layer2 = nn.Linear(hidden_size, hidden_size)
        self.output = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.layer1(x)
        x = self.relu(x)
        x = self.layer2(x)
        x = self.relu(x)
        x = self.output(x)
        x = self.sigmoid(x)
        return x

def train_model(X_train, y_train, X_val, y_val, input_size, model_path, epochs=100, batch_size=32, learning_rate=0.001):
    """Trains a simple neural network model and saves it."""
    try:
        # Convert data to tensors
        X_train_tensor = torch.FloatTensor(X_train)
        y_train_tensor = torch.FloatTensor(y_train).view(-1, 1)
        X_val_tensor = torch.FloatTensor(X_val)
        y_val_tensor = torch.FloatTensor(y_val).view(-1, 1)

        # Initialize model, loss, and optimizer
        model = SimpleNN(input_size)
        criterion = nn.BCELoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)

        # Training loop
        metrics = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}
        for epoch in range(epochs):
            model.train()
            for i in range(0, len(X_train_tensor), batch_size):
                batch_X = X_train_tensor[i:i + batch_size]
                batch_y = y_train_tensor[i:i + batch_size]

                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()

            # Calculate training metrics
            model.eval()
            with torch.no_grad():
                train_outputs = model(X_train_tensor)
                train_loss = criterion(train_outputs, y_train_tensor).item()
                train_pred = (train_outputs > 0.5).float()
                train_acc = (train_pred == y_train_tensor).float().mean().item()

                val_outputs = model(X_val_tensor)
                val_loss = criterion(val_outputs, y_val_tensor).item()
                val_pred = (val_outputs > 0.5).float()
                val_acc = (val_pred == y_val_tensor).float().mean().item()

            metrics['train_loss'].append(train_loss)
            metrics['val_loss'].append(val_loss)
            metrics['train_acc'].append(train_acc)
            metrics['val_acc'].append(val_acc)

            logger_main.info(f"Epoch {epoch+1}/{epochs}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}, train_acc={train_acc:.4f}, val_acc={val_acc:.4f}")

        # Save the model
        torch.save(model.state_dict(), model_path)
        logger_main.info(f"Saved model to {model_path}")

        # Save metrics to a file
        os.makedirs('training_metrics', exist_ok=True)
        metrics_file = f"training_metrics/{os.path.basename(model_path)}_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=4)
        logger_main.info(f"Saved training metrics to {metrics_file}")

        return True
    except Exception as e:
        logger_main.error(f"Error training model: {e}")
        return False

__all__ = ['train_model']
