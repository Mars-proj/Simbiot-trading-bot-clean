from logging_setup import logger_main
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split

async def train_model(data, model_path, num_epochs=100, learning_rate=0.01, train_split=0.8):
    """Trains an ML model with the provided data."""
    try:
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Data must be a pandas DataFrame, got {type(data)}")
            return None
        if 'label' not in data.columns:
            logger_main.error("Data must contain a 'label' column for training")
            return None

        # Define a more complex model
        class DeepModel(nn.Module):
            def __init__(self, input_size):
                super(DeepModel, self).__init__()
                self.layer1 = nn.Linear(input_size, 64)
                self.relu1 = nn.ReLU()
                self.layer2 = nn.Linear(64, 32)
                self.relu2 = nn.ReLU()
                self.layer3 = nn.Linear(32, 1)
                self.sigmoid = nn.Sigmoid()

            def forward(self, x):
                x = self.layer1(x)
                x = self.relu1(x)
                x = self.layer2(x)
                x = self.relu2(x)
                x = self.layer3(x)
                x = self.sigmoid(x)
                return x

        # Split data into training and validation sets
        train_data, val_data = train_test_split(data, train_size=train_split, random_state=42)
        X_train = torch.tensor(train_data.drop(columns=['label']).values, dtype=torch.float32)
        y_train = torch.tensor(train_data['label'].values, dtype=torch.float32).unsqueeze(1)
        X_val = torch.tensor(val_data.drop(columns=['label']).values, dtype=torch.float32)
        y_val = torch.tensor(val_data['label'].values, dtype=torch.float32).unsqueeze(1)

        # Initialize model
        model = DeepModel(input_size=X_train.shape[1])
        criterion = nn.BCELoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)

        # Training loop
        for epoch in range(num_epochs):
            model.train()
            optimizer.zero_grad()
            outputs = model(X_train)
            loss = criterion(outputs, y_train)
            loss.backward()
            optimizer.step()

            # Validation
            model.eval()
            with torch.no_grad():
                val_outputs = model(X_val)
                val_loss = criterion(val_outputs, y_val)

            if (epoch + 1) % 10 == 0:
                logger_main.info(f"Epoch [{epoch+1}/{num_epochs}], Train Loss: {loss.item():.4f}, Val Loss: {val_loss.item():.4f}")

        # Save model
        torch.save(model, model_path)
        logger_main.info(f"Model trained and saved to {model_path}")
        return model
    except Exception as e:
        logger_main.error(f"Error training model: {e}")
        return None

__all__ = ['train_model']
