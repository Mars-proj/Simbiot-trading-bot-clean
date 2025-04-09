from sklearn.ensemble import RandomForestClassifier
import joblib
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

def train_random_forest(X, y, model_path="rf_model.pkl"):
    """
    Train a Random Forest model.

    Args:
        X (np.ndarray): Features.
        y (np.ndarray): Target.
        model_path (str): Path to save the model (default: 'rf_model.pkl').

    Returns:
        Trained model.
    """
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    joblib.dump(model, model_path)
    return model

def train_lstm_model(X, y, model_path="lstm_model.h5"):
    """
    Train an LSTM model.

    Args:
        X (np.ndarray): Features (shape: [samples, timesteps, features]).
        y (np.ndarray): Target.
        model_path (str): Path to save the model (default: 'lstm_model.h5').

    Returns:
        Trained model.
    """
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
        Dropout(0.2),
        LSTM(50),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(X, y, epochs=50, batch_size=32, validation_split=0.2)
    model.save(model_path)
    return model
