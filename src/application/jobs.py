from src.infrastructure.database.session import SessionLocal
from src.infrastructure.repositories.election_repository import SqlAlchemyElectionRepository
import logging

# Loglama görebilmek için basit bir konfigürasyon
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_election_job(election_id: int):
    """Seçimi başlatan arka plan görevi"""
    db = SessionLocal()
    try:
        repo = SqlAlchemyElectionRepository(db)
        repo.start_election(election_id)
        logger.info(f"JOB: Election {election_id} has been STARTED automatically.")
    except Exception as e:
        logger.error(f"JOB ERROR (Start Election {election_id}): {str(e)}")
    finally:
        db.close()

def end_election_job(election_id: int):
    """Seçimi bitiren arka plan görevi"""
    db = SessionLocal()
    try:
        repo = SqlAlchemyElectionRepository(db)
        repo.end_election(election_id)
        logger.info(f"JOB: Election {election_id} has been ENDED automatically.")
    except Exception as e:
        logger.error(f"JOB ERROR (End Election {election_id}): {str(e)}")
    finally:
        db.close()