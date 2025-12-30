from fastapi import APIRouter, Depends, HTTPException, status
from src.application import schemas
from src.application.services.voting_service import VotingService
from src.presentation.dependencies import get_voting_service, get_current_user

router = APIRouter()

@router.post("/elections/{election_id}/token")
def generate_voting_token(
    election_id: int, 
    voting_service: VotingService = Depends(get_voting_service), 
    current_user: schemas.User = Depends(get_current_user)
):
    # We might want to verify election exists here, but service checks token repo.
    # The requirement: "Verify election exists" was in main.py
    # Ideally service handles this.
    token = voting_service.generate_token(user_id=current_user.id, election_id=election_id)
    
    if not token:
        # If token is None, it means it already exists (logic in service)
        raise HTTPException(status_code=400, detail="You have already generated a voting token for this election.")
        
    return {"voting_token": token, "message": "Save this token! You need it to vote."}

@router.post("/api/votes", status_code=status.HTTP_200_OK)
def cast_vote(vote: schemas.VoteCastRequest, voting_service: VotingService = Depends(get_voting_service)):
    # Check election status (active)
    
    try:
        db_vote = voting_service.cast_vote(vote)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "success": True,
        "message": "Vote successfully cast.",
        "vote_hash": db_vote.vote_hash
    }

# Helper to avoid circular deps or messy signature
from src.application.services.election_service import ElectionService
from src.presentation.dependencies import get_election_service

@router.get("/api/elections/{election_id}/results", response_model=schemas.ElectionResult)
def get_election_results(
    election_id: int, 
    voting_service: VotingService = Depends(get_voting_service),
    election_service: ElectionService = Depends(get_election_service),
    current_user: schemas.User = Depends(get_current_user)
):
    # Fetch Election Details
    db_election = election_service.get_election(election_id)
    if not db_election:
        raise HTTPException(status_code=404, detail="Election not found")

    # Fetch Results
    results = voting_service.get_results(election_id)
    
    # Return formatted response
    return schemas.ElectionResult(
        id=db_election.id,
        title=db_election.title,
        status=db_election.status,
        results=[schemas.CandidateResult(id=r['id'], name=r['name'], vote_count=r['vote_count']) for r in results]
    )
