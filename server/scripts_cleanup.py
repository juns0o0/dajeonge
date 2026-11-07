"""보관 기간이 지난 음성 파일 정리. cron 으로 하루 1회:  cd server && python3 -c "from scripts_cleanup import purge_audio; purge_audio()" """
import os, sys
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from app.db import SessionLocal
from app.models import Conversation, Family


def purge_audio(dry_run: bool = False) -> int:
    db = SessionLocal(); n = 0
    try:
        rows = db.query(Conversation, Family).join(Family, Family.id == Conversation.family_id).filter(Conversation.audio_path.isnot(None)).all()
        for c, f in rows:
            if c.started_at < datetime.utcnow() - timedelta(days=f.keep_audio_days or 30):
                p = Path(c.audio_path)
                if p.exists() and not dry_run:
                    p.unlink()
                c.audio_path = None; n += 1
        if not dry_run:
            db.commit()
    finally:
        db.close()
    print(f"purged audio files: {n}")
    return n


if __name__ == "__main__":
    purge_audio("--dry-run" in sys.argv)
