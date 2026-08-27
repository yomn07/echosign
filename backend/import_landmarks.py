import json
from pathlib import Path

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import Landmark


FILE1 = Path("backend/landmarks.json")
FILE2 = Path("backend/landmarksletters.json")
BATCH_SIZE = 5


def import_landmarks(JSON_FILE):
    if not JSON_FILE.exists():
        print(f"File not found: {JSON_FILE}")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Found {len(data)} landmarks")

    db: Session = SessionLocal()

    try:
        batch = []

        for i, (text, landmarks) in enumerate(data.items(), start=1):

            landmark = Landmark(
                text=text,
                landmarks=landmarks
            )

            batch.append(landmark)

            if len(batch) >= BATCH_SIZE:
                db.add_all(batch)
                db.commit()

                print(f"Imported {i}/{len(data)}")

                batch.clear()

        # Remaining rows
        if batch:
            db.add_all(batch)
            db.commit()

        print("Import completed successfully!")

    except Exception as e:
        db.rollback()
        print("Import failed:")
        print(e)

    finally:
        db.close()


if __name__ == "__main__":
    import_landmarks(FILE1)
    import_landmarks(FILE2)