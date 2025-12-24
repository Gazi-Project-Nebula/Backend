from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import random

# Schemas
from src.application import schemas

# Services & Repositories
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.repositories.election_repository import SqlAlchemyElectionRepository, SqlAlchemyCandidateRepository
from src.infrastructure.repositories.vote_repository import SqlAlchemyVotingTokenRepository
from src.application.services.auth_service import AuthService
from src.application.services.election_service import ElectionService

def seed_database(db: Session):
    """
    Populates the database with extensive mock data if it is empty.
    Creates Admins, Voters, and multiple Elections with realistic scenarios.
    """
    print("🌱 Checking database state...")
    
    user_repo = SqlAlchemyUserRepository(db)
    
    # Idempotency check: If admin exists, assume seeded.
    if user_repo.get_by_username("admin"):
        print("✅ Database already seeded. Skipping.")
        return

    print("⚡ Seeding database with RICH mock data...")

    # --- 1. SETUP SERVICES ---
    auth_service = AuthService(user_repo)
    election_repo = SqlAlchemyElectionRepository(db)
    candidate_repo = SqlAlchemyCandidateRepository(db)
    token_repo = SqlAlchemyVotingTokenRepository(db)
    election_service = ElectionService(election_repo, candidate_repo, token_repo, user_repo)

    # --- 2. CREATE USERS ---
    print("   --> Creating Users...")
    
    # 2.1 Admins
    admins = ["admin", "moderator"]
    created_admins = []
    for adm in admins:
        user = auth_service.register_user(schemas.UserCreate(username=adm, password="password123"))
        auth_service.update_user_role(user.id, "admin")
        created_admins.append(user)
        print(f"      - Admin: {adm}")

    # 2.2 Voters (Increased Count & Variety)
    # Generate 50 realistic usernames
    base_names = [
        "alice", "bob", "charlie", "david", "eve", "frank", "grace", "heidi", "ivan", "judy",
        "mallory", "oscar", "peggy", "sybil", "trent", "walter", "victor", "zoe", "neo", "trinity",
        "mario", "luigi", "peach", "bowser", "zelda", "link", "ganon", "samus", "kirby", "dk",
        "snake", "cloud", "tifa", "aerith", "sephiroth", "goku", "vegeta", "naruto", "sasuke", "luffy",
        "zoro", "nami", "sanji", "usopp", "chopper", "robin", "franky", "brook", "jinbe", "yamato"
    ]
    
    # Ensure we have enough unique names, if not, append numbers
    voter_names = []
    for i in range(50):
        if i < len(base_names):
            voter_names.append(base_names[i])
        else:
            voter_names.append(f"voter_{i+1}")
    
    for v_name in voter_names:
        if not user_repo.get_by_username(v_name):
             auth_service.register_user(schemas.UserCreate(username=v_name, password="password123"))
    
    print(f"      - Created/Verified {len(voter_names)} voters.")

    # --- 3. CREATE ELECTIONS ---
    print("   --> Creating Elections...")

    # Data Source (Expanded & Improved)
    elections_data = [
        {
            "title": "Student Council President 2025",
            "desc": "Vote for the student who will lead the council this year. Looking for strong leadership and vision.",
            "candidates": [
                {"name": "Alice Johnson", "bio": "Focus: Sustainability & Campus Greenery"},
                {"name": "Bob Smith", "bio": "Focus: Better Cafeteria Food & Lower Prices"},
                {"name": "Charlie Brown", "bio": "Focus: More Social Events & Networking"}
            ],
            "days_active": 7,
            "status": "active"
        },
        {
            "title": "Best Programming Language 2024",
            "desc": "The eternal tech debate. Which language dominates the industry right now?",
            "candidates": [
                {"name": "Python", "bio": "Known for: Data Science & AI dominance."},
                {"name": "Rust", "bio": "Known for: Memory safety & Blazing speed."},
                {"name": "Go", "bio": "Known for: Cloud native & Concurrency."},
                {"name": "TypeScript", "bio": "Known for: Frontend supremacy."},
                {"name": "Java", "bio": "Known for: Enterprise stability."}
            ],
            "days_active": 14,
            "status": "active"
        },
        {
            "title": "Friday Office Lunch",
            "desc": "We are ordering food this Friday. What should the team get?",
            "candidates": [
                {"name": "Pizza Hut", "bio": "Classic choice. Pepperoni & Veggie options."},
                {"name": "Sushi Palace", "bio": "Fresh & Light. Rolls & Sashimi."},
                {"name": "Taco Stand", "bio": "Spicy & Fun. Tacos & Burritos."},
                {"name": "Burger Joint", "bio": "Hearty & Filling. Burgers & Fries."}
            ],
            "days_active": 2,
            "status": "active"
        },
        {
            "title": "Hackathon 2025 Theme",
            "desc": "Help us decide the focus area for the upcoming global hackathon.",
            "candidates": [
                {"name": "AI & Generative Models", "bio": "Building the next ChatGPT wrappers."},
                {"name": "Blockchain & Web3", "bio": "Decentralized apps and smart contracts."},
                {"name": "Climate Tech", "bio": "Solutions for a sustainable future."},
                {"name": "FinTech", "bio": "Revolutionizing banking and payments."}
            ],
            "days_active": 30,
            "status": "pending" # Future election
        },
        {
            "title": "Movie Night Selection",
            "desc": "Pick the movie for this weekend's community stream on Discord.",
            "candidates": [
                {"name": "Inception", "bio": "Sci-Fi Thriller by Nolan."},
                {"name": "The Matrix", "bio": "Classic Cyberpunk Action."},
                {"name": "Interstellar", "bio": "Space Exploration Drama."},
                {"name": "Spider-Man: Into the Spider-Verse", "bio": "Animated Masterpiece."}
            ],
            "days_active": 3,
            "status": "completed" # Past election
        },
        {
            "title": "Next Feature to Build",
            "desc": "Our product roadmap is flexible. What feature do you want to see next?",
            "candidates": [
                {"name": "Dark Mode", "bio": "Easy on the eyes for night owls."},
                {"name": "Mobile App", "bio": "Android & iOS native support."},
                {"name": "Email Notifications", "bio": "Get alerted on updates."},
                {"name": "Public API V2", "bio": "Better documentation & endpoints."}
            ],
            "days_active": 10,
            "status": "active"
        },
        {
            "title": "Company Retreat Location",
            "desc": "Where should the team go for the annual retreat?",
            "candidates": [
                {"name": "Mountain Cabin", "bio": "Hiking, campfires, and nature."},
                {"name": "Beach Resort", "bio": "Sun, sand, and cocktails."},
                {"name": "City Break (NYC)", "bio": "Broadway, museums, and nightlife."},
                {"name": "Lake House", "bio": "Boating, fishing, and relaxation."}
            ],
            "days_active": 20,
            "status": "active"
        },
        {
            "title": "Best Superpower",
            "desc": "If you could pick one, what would it be?",
            "candidates": [
                {"name": "Flight", "bio": "Travel anywhere instantly."},
                {"name": "Invisibility", "bio": "Go anywhere unseen."},
                {"name": "Teleportation", "bio": "Be anywhere instantly."},
                {"name": "Time Travel", "bio": "Fix mistakes or see the future."}
            ],
            "days_active": 5,
            "status": "active"
        },
        {
            "title": "Game of the Year",
            "desc": "Community vote for the best game released recently.",
            "candidates": [
                {"name": "Elden Ring", "bio": "Open world masterpiece."},
                {"name": "Baldur's Gate 3", "bio": "D&D RPG perfection."},
                {"name": "Zelda: TOTK", "bio": "Creative physics sandbox."},
                {"name": "God of War Ragnarok", "bio": "Epic storytelling."}
            ],
            "days_active": 15,
            "status": "active"
        },
        {
            "title": "New Logo Design",
            "desc": "The design team submitted 3 options. Pick your favorite.",
            "candidates": [
                {"name": "Option A (Minimalist)", "bio": "Clean lines, modern look."},
                {"name": "Option B (Retro)", "bio": "80s synthwave vibe."},
                {"name": "Option C (Futuristic)", "bio": "Cyberpunk neon style."}
            ],
            "days_active": 7,
            "status": "active"
        },
        {
            "title": "Remote Work Policy",
            "desc": "Deciding on the hybrid work model for the next year.",
            "candidates": [
                {"name": "Fully Remote", "bio": "Work from anywhere, anytime."},
                {"name": "Hybrid (2 days office)", "bio": "Balance of social and focus time."},
                {"name": "Office First", "bio": "Maximize collaboration and culture."}
            ],
            "days_active": 14,
            "status": "active"
        },
        {
            "title": "Team Mascot",
            "desc": "We need a mascot for our internal hackathon team!",
            "candidates": [
                {"name": "The Cyber Cat", "bio": "Agile and mysterious."},
                {"name": "The Robo Rex", "bio": "Powerful and unstoppable."},
                {"name": "The Pixel Penguin", "bio": "Cool and collected."}
            ],
            "days_active": 5,
            "status": "active"
        },
        {
            "title": "Charity Fundraiser",
            "desc": "Which charity should we support this quarter?",
            "candidates": [
                {"name": "Local Animal Shelter", "bio": "Helping pets find homes."},
                {"name": "Food Bank", "bio": "Feeding the community."},
                {"name": "Code for Kids", "bio": "Teaching the next generation."}
            ],
            "days_active": 30,
            "status": "active"
        }
    ]

    # Create Loop
    primary_admin = created_admins[0]
    
    for data in elections_data:
        start_time = datetime.now(timezone.utc)
        
        # Adjust start time based on desired status logic
        if data["status"] == "pending":
             # Starts in future
             start_time = datetime.now(timezone.utc) + timedelta(days=1)
        elif data["status"] == "completed":
             # Started in past
             start_time = datetime.now(timezone.utc) - timedelta(days=data["days_active"] + 1)

        end_time = start_time + timedelta(days=data["days_active"])

        election_create = schemas.ElectionCreate(
            title=data["title"],
            description=data["desc"],
            start_time=start_time,
            end_time=end_time,
            candidates=[
                schemas.CandidateCreate(name=c["name"], bio=c["bio"]) for c in data["candidates"]
            ]
        )
        
        # Create via Service (Handles Token Generation)
        election = election_service.create_election(election_create, user_id=primary_admin.id)
        
        # Apply Status Logic
        if data["status"] == "active":
             election_service.start_election(election.id)
        elif data["status"] == "completed":
             # We assume it was active then ended
             election_service.start_election(election.id)
             election_service.end_election(election.id)
        
        print(f"      - [{data['status'].upper()}] {election.title}")

    print("✅ Seeding completed successfully!")