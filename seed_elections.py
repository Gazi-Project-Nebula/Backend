from database import SessionLocal
import crud, schemas
from datetime import datetime, timedelta, timezone

def seed_data():
    db = SessionLocal()
    
    # 1. Get the admin user
    admin = crud.get_user_by_username(db, "admin")
    if not admin:
        print("Error: User 'admin' not found. Please run create_admin.py first.")
        return

    print(f"Creating 10 elections for admin: {admin.username}...\n")

    # List of 10 Election Data Dictionaries
    elections_data = [
        {
            "title": "Student Council President 2025",
            "desc": "Vote for the student who will lead the council this year.",
            "candidates": ["Alice Johnson", "Bob Smith", "Charlie Brown"],
            "bio_prefix": "Campaign promise: "
        },
        {
            "title": "Best Programming Language",
            "desc": "The eternal debate. Which one rules the backend?",
            "candidates": ["Python", "Rust", "Go", "TypeScript", "Java"],
            "bio_prefix": "Known for: "
        },
        {
            "title": "Friday Office Lunch",
            "desc": "We are ordering food this Friday. What should we get?",
            "candidates": ["Pizza Hut", "Sushi Palace", "Taco Stand", "Burger Joint"],
            "bio_prefix": "Menu highlight: "
        },
        {
            "title": "Hackathon 2025 Theme",
            "desc": "Help us decide the focus area for the upcoming hackathon.",
            "candidates": ["AI & Machine Learning", "Blockchain & Web3", "Sustainability", "FinTech"],
            "bio_prefix": "Focus on: "
        },
        {
            "title": "Movie Night Selection",
            "desc": "Pick the movie for this weekend's community stream.",
            "candidates": ["Inception", "The Matrix", "Interstellar", "Spider-Man: Into the Spider-Verse"],
            "bio_prefix": "Genre: "
        },
        {
            "title": "Next Feature to Build",
            "desc": "Our roadmap is flexible. What do you want to see next?",
            "candidates": ["Dark Mode", "Mobile App", "Email Notifications", "Public API V2"],
            "bio_prefix": "Impact: "
        },
        {
            "title": "Company Retreat Location",
            "desc": "Where should the team go for the annual retreat?",
            "candidates": ["Mountain Cabin", "Beach Resort", "City Break (NYC)", "Lake House"],
            "bio_prefix": "Vibe: "
        },
        {
            "title": "Best Superpower",
            "desc": "If you could pick one, what would it be?",
            "candidates": ["Flight", "Invisibility", "Teleportation", "Time Travel"],
            "bio_prefix": "Pro: "
        },
        {
            "title": "Game of the Year",
            "desc": "Community vote for the best game released recently.",
            "candidates": ["Elden Ring", "Baldur's Gate 3", "Zelda: TOTK", "God of War"],
            "bio_prefix": "Rating: "
        },
        {
            "title": "New Logo Design",
            "desc": "The design team submitted 3 options. Pick your favorite.",
            "candidates": ["Option A (Minimalist)", "Option B (Retro)", "Option C (Futuristic)"],
            "bio_prefix": "Style: "
        }
    ]

    # Loop through and create them
    for i, data in enumerate(elections_data):
        # Create Schema
        election_create = schemas.ElectionCreate(
            title=data["title"],
            description=data["desc"],
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=7), # All end in 7 days
            candidates=[
                schemas.CandidateCreate(name=c, bio=f"{data['bio_prefix']} Great choice!") for c in data["candidates"]
            ]
        )
        
        # Save to DB
        db_election = crud.create_election(db, election_create, admin.id)
        
        # Make Active Immediately
        crud.start_election(db, db_election.id)
        
        print(f"[{i+1}/10] Created: {data['title']}")

    db.close()
    print("\n✅ Success! 10 Elections created. Refresh your Frontend Dashboard.")

if __name__ == "__main__":
    seed_data()