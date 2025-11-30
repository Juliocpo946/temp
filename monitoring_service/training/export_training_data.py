import os
import json
import numpy as np
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.training_sample_repository import TrainingSampleRepository

class TrainingDataExporter:
    def __init__(self, output_dir: str = "training/data/production"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export(self, source: str = "production", limit: int = 10000):
        db = SessionLocal()
        try:
            repo = TrainingSampleRepository(db)
            samples = repo.get_for_training(source, limit)

            if not samples:
                print("[WARN] No hay muestras disponibles para exportar")
                return

            sequences = []
            contexts = []
            labels = []
            sample_ids = []

            for sample in samples:
                window_data = sample.window_data.get("sequence", [])
                context_data = sample.context_data.get("context", [])

                if len(window_data) == 30 and len(context_data) == 6:
                    sequences.append(window_data)
                    contexts.append(context_data)
                    labels.append(sample.label)
                    sample_ids.append(str(sample.id))

            if not sequences:
                print("[WARN] No hay muestras validas para exportar")
                return

            sequences = np.array(sequences, dtype=np.float32)
            contexts = np.array(contexts, dtype=np.float32)
            labels = np.array(labels, dtype=np.int32)

            np.save(os.path.join(self.output_dir, "sequences.npy"), sequences)
            np.save(os.path.join(self.output_dir, "contexts.npy"), contexts)
            np.save(os.path.join(self.output_dir, "labels.npy"), labels)

            with open(os.path.join(self.output_dir, "sample_ids.json"), "w") as f:
                json.dump(sample_ids, f)

            print(f"[INFO] Exportadas {len(labels)} muestras a {self.output_dir}")
            print(f"[INFO] Distribucion de clases: {np.bincount(labels)}")

            repo.mark_as_used(sample_ids)
            print("[INFO] Muestras marcadas como usadas")

        finally:
            db.close()


if __name__ == "__main__":
    exporter = TrainingDataExporter()
    exporter.export()