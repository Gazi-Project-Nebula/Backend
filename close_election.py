from database import SessionLocal, Election
from datetime import datetime, timedelta, timezone

def force_close_election():
    db = SessionLocal()
    
    # 1. Ask which election to close
    election_id = input("Enter the ID of the election to close (e.g., 1): ")
    
    # 2. Find the election
    election = db.query(Election).filter(Election.id == election_id).first()
    
    if not election:
        print("❌ Election not found!")
        return

    # 3. Update the data
    print(f"Closing election: {election.title}...")
    
    # FIX: We use datetime.now(timezone.utc) to make it "Timezone Aware"
    election.end_time = datetime.now(timezone.utc) - timedelta(days=1)
    
    # Force status to completed
    election.status = "completed"
    
    # 4. Save
    db.commit()
    print("✅ Election closed! Refresh your dashboard to see results.")
    db.close()

if __name__ == "__main__":
    force_close_election()