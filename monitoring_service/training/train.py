import os
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers, Model
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.model_selection import train_test_split

class InterventionModelTrainer:
    SEQUENCE_LENGTH = 30
    FEATURE_COUNT = 16
    CONTEXT_COUNT = 6
    NUM_CLASSES = 4

    def __init__(self, data_dir: str = "training/data/synthetic", model_dir: str = "models"):
        self.data_dir = data_dir
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

    def load_data(self):
        sequences = np.load(os.path.join(self.data_dir, "sequences.npy"))
        contexts = np.load(os.path.join(self.data_dir, "contexts.npy"))
        labels = np.load(os.path.join(self.data_dir, "labels.npy"))
        return sequences, contexts, labels

    def build_model(self) -> Model:
        sequence_input = layers.Input(shape=(self.SEQUENCE_LENGTH, self.FEATURE_COUNT), name="sequence_input")
        context_input = layers.Input(shape=(self.CONTEXT_COUNT,), name="context_input")

        x = layers.GRU(64, return_sequences=True)(sequence_input)
        x = layers.Dropout(0.3)(x)
        x = layers.GRU(32)(x)
        x = layers.Dropout(0.3)(x)

        context_dense = layers.Dense(16, activation="relu")(context_input)

        combined = layers.Concatenate()([x, context_dense])
        combined = layers.Dense(32, activation="relu")(combined)
        combined = layers.Dropout(0.3)(combined)
        output = layers.Dense(self.NUM_CLASSES, activation="softmax")(combined)

        model = Model(inputs=[sequence_input, context_input], outputs=output)
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"]
        )
        return model

    def train(self, epochs: int = 50, batch_size: int = 32):
        print("[INFO] Cargando datos...")
        sequences, contexts, labels = self.load_data()

        X_seq_train, X_seq_test, X_ctx_train, X_ctx_test, y_train, y_test = train_test_split(
            sequences, contexts, labels, test_size=0.2, random_state=42, stratify=labels
        )

        print(f"[INFO] Train: {len(y_train)} muestras")
        print(f"[INFO] Test: {len(y_test)} muestras")

        model = self.build_model()
        model.summary()

        callbacks = [
            EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True),
            ModelCheckpoint(
                os.path.join(self.model_dir, "intervention_model.keras"),
                monitor="val_accuracy",
                save_best_only=True
            )
        ]

        print("[INFO] Iniciando entrenamiento...")
        history = model.fit(
            [X_seq_train, X_ctx_train],
            y_train,
            validation_data=([X_seq_test, X_ctx_test], y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks
        )

        print("[INFO] Evaluando modelo...")
        loss, accuracy = model.evaluate([X_seq_test, X_ctx_test], y_test)
        print(f"[INFO] Test Loss: {loss:.4f}")
        print(f"[INFO] Test Accuracy: {accuracy:.4f}")

        return model, history


if __name__ == "__main__":
    trainer = InterventionModelTrainer()
    model, history = trainer.train()
    print("[INFO] Entrenamiento completado")