import numpy as np
import json
import os
from typing import List, Tuple

class DatasetGenerator:
    SEQUENCE_LENGTH = 30
    FEATURE_COUNT = 16
    CONTEXT_COUNT = 6
    SAMPLES_PER_CLASS = 2500

    def __init__(self, output_dir: str = "training/data/synthetic"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        sequences = []
        contexts = []
        labels = []

        for _ in range(self.SAMPLES_PER_CLASS):
            seq, ctx = self._generate_no_intervention()
            sequences.append(seq)
            contexts.append(ctx)
            labels.append(0)

        for _ in range(self.SAMPLES_PER_CLASS):
            seq, ctx = self._generate_vibration()
            sequences.append(seq)
            contexts.append(ctx)
            labels.append(1)

        for _ in range(self.SAMPLES_PER_CLASS):
            seq, ctx = self._generate_instruction()
            sequences.append(seq)
            contexts.append(ctx)
            labels.append(2)

        for _ in range(self.SAMPLES_PER_CLASS):
            seq, ctx = self._generate_pause()
            sequences.append(seq)
            contexts.append(ctx)
            labels.append(3)

        sequences = np.array(sequences, dtype=np.float32)
        contexts = np.array(contexts, dtype=np.float32)
        labels = np.array(labels, dtype=np.int32)

        indices = np.random.permutation(len(labels))
        sequences = sequences[indices]
        contexts = contexts[indices]
        labels = labels[indices]

        return sequences, contexts, labels

    def _generate_base_frame(self) -> np.ndarray:
        frame = np.zeros(self.FEATURE_COUNT, dtype=np.float32)
        frame[0] = np.random.uniform(0.3, 0.8)
        frame[1] = np.random.uniform(0.1, 0.4)
        frame[2] = np.random.uniform(0.0, 0.1)
        frame[3] = np.random.uniform(0.0, 0.05)
        frame[4] = np.random.uniform(0.0, 0.05)
        frame[5] = np.random.uniform(0.0, 0.03)
        frame[6] = np.random.uniform(0.0, 0.03)
        frame[7] = np.random.uniform(0.0, 0.05)
        frame[8] = 1.0
        frame[9] = np.random.uniform(-0.1, 0.1)
        frame[10] = np.random.uniform(-0.1, 0.1)
        frame[11] = 0.0
        frame[12] = np.random.uniform(0.25, 0.4)
        frame[13] = 1.0
        frame[14] = np.random.uniform(0.7, 1.0)
        frame[15] = np.random.uniform(0.6, 0.9)
        return frame

    def _generate_no_intervention(self) -> Tuple[np.ndarray, np.ndarray]:
        sequence = np.array([self._generate_base_frame() for _ in range(self.SEQUENCE_LENGTH)])
        noise = np.random.uniform(-0.05, 0.05, sequence.shape)
        sequence = np.clip(sequence + noise, 0, 1)
        sequence[:, 8] = 1.0
        sequence[:, 11] = 0.0
        sequence[:, 13] = 1.0
        context = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        return sequence, context

    def _generate_vibration(self) -> Tuple[np.ndarray, np.ndarray]:
        sequence = np.array([self._generate_base_frame() for _ in range(self.SEQUENCE_LENGTH)])
        distraction_type = np.random.choice(["not_looking", "drowsy", "no_face"])
        
        if distraction_type == "not_looking":
            distracted_frames = np.random.choice(self.SEQUENCE_LENGTH, size=np.random.randint(5, 12), replace=False)
            sequence[distracted_frames, 8] = 0.0
            sequence[distracted_frames, 9] = np.random.uniform(0.3, 0.8, len(distracted_frames))
            sequence[distracted_frames, 10] = np.random.uniform(0.3, 0.8, len(distracted_frames))
        elif distraction_type == "drowsy":
            drowsy_frames = np.random.choice(self.SEQUENCE_LENGTH, size=np.random.randint(5, 12), replace=False)
            sequence[drowsy_frames, 11] = np.random.uniform(0.3, 0.8, len(drowsy_frames))
            sequence[drowsy_frames, 12] = np.random.uniform(0.1, 0.2, len(drowsy_frames))
        else:
            no_face_frames = np.random.choice(self.SEQUENCE_LENGTH, size=np.random.randint(5, 10), replace=False)
            sequence[no_face_frames, 13] = 0.0

        context = np.array([
            np.random.uniform(0.5, 1.0),
            np.random.uniform(0.5, 1.0),
            np.random.uniform(0.5, 1.0),
            np.random.uniform(0.0, 0.2),
            0.0,
            0.0
        ], dtype=np.float32)
        return sequence, context

    def _generate_instruction(self) -> Tuple[np.ndarray, np.ndarray]:
        sequence = np.array([self._generate_base_frame() for _ in range(self.SEQUENCE_LENGTH)])
        frustration_start = np.random.randint(5, 15)
        
        for i in range(frustration_start, self.SEQUENCE_LENGTH):
            progress = (i - frustration_start) / (self.SEQUENCE_LENGTH - frustration_start)
            sequence[i, 0] = max(0.1, sequence[i, 0] - progress * 0.5)
            sequence[i, 3] = min(0.8, progress * 0.6 + np.random.uniform(0, 0.2))
            sequence[i, 4] = min(0.5, progress * 0.3 + np.random.uniform(0, 0.1))
            sequence[i, 5] = min(0.4, progress * 0.2 + np.random.uniform(0, 0.1))
            sequence[i, 7] = min(0.5, progress * 0.3 + np.random.uniform(0, 0.1))
            sequence[i, 14] = max(0.0, 1.0 - progress * 0.8)

        context = np.array([
            np.random.uniform(0.3, 1.0),
            np.random.uniform(0.5, 1.0),
            np.random.uniform(0.5, 1.0),
            np.random.uniform(0.0, 0.3),
            0.0,
            0.0
        ], dtype=np.float32)
        return sequence, context

    def _generate_pause(self) -> Tuple[np.ndarray, np.ndarray]:
        pause_type = np.random.choice(["persistent_frustration", "persistent_distraction", "persistent_drowsiness"])
        
        if pause_type == "persistent_frustration":
            sequence, _ = self._generate_instruction()
            for i in range(self.SEQUENCE_LENGTH):
                sequence[i, 3] = min(0.9, sequence[i, 3] + 0.2)
                sequence[i, 4] = min(0.6, sequence[i, 4] + 0.1)
            context = np.array([
                np.random.uniform(0.2, 0.5),
                np.random.uniform(0.1, 0.3),
                np.random.uniform(0.5, 1.0),
                np.random.uniform(0.1, 0.3),
                np.random.uniform(0.1, 0.3),
                0.0
            ], dtype=np.float32)
        elif pause_type == "persistent_distraction":
            sequence, _ = self._generate_vibration()
            distracted_frames = np.random.choice(self.SEQUENCE_LENGTH, size=np.random.randint(15, 25), replace=False)
            sequence[distracted_frames, 8] = 0.0
            sequence[distracted_frames, 13] = np.random.choice([0.0, 1.0], len(distracted_frames))
            context = np.array([
                np.random.uniform(0.1, 0.3),
                np.random.uniform(0.5, 1.0),
                np.random.uniform(0.5, 1.0),
                np.random.uniform(0.2, 0.5),
                0.0,
                0.0
            ], dtype=np.float32)
        else:
            sequence, _ = self._generate_vibration()
            drowsy_frames = np.random.choice(self.SEQUENCE_LENGTH, size=np.random.randint(15, 25), replace=False)
            sequence[drowsy_frames, 11] = np.random.uniform(0.5, 1.0, len(drowsy_frames))
            sequence[drowsy_frames, 12] = np.random.uniform(0.05, 0.15, len(drowsy_frames))
            context = np.array([
                np.random.uniform(0.1, 0.3),
                np.random.uniform(0.5, 1.0),
                np.random.uniform(0.5, 1.0),
                np.random.uniform(0.2, 0.5),
                0.0,
                0.0
            ], dtype=np.float32)

        return sequence, context

    def save(self, sequences: np.ndarray, contexts: np.ndarray, labels: np.ndarray) -> None:
        np.save(os.path.join(self.output_dir, "sequences.npy"), sequences)
        np.save(os.path.join(self.output_dir, "contexts.npy"), contexts)
        np.save(os.path.join(self.output_dir, "labels.npy"), labels)
        print(f"[INFO] Dataset guardado en {self.output_dir}")
        print(f"[INFO] Secuencias: {sequences.shape}")
        print(f"[INFO] Contextos: {contexts.shape}")
        print(f"[INFO] Labels: {labels.shape}")
        print(f"[INFO] Distribucion de clases: {np.bincount(labels)}")


if __name__ == "__main__":
    generator = DatasetGenerator()
    sequences, contexts, labels = generator.generate()
    generator.save(sequences, contexts, labels)