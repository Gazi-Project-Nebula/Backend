from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from src.application import schemas
from src.application.services.election_service import ElectionService
from src.presentation.dependencies import get_election_service, get_current_user, verify_admin_user, verify_election_manager

router = APIRouter()

@router.post("/api/elections", status_code=status.HTTP_201_CREATED)
def create_election(
    election_request: schemas.ElectionCreateRequest, 
    election_service: ElectionService = Depends(get_election_service), 
    current_user: schemas.User = Depends(get_current_user)
):
    # Mapping request to schema
    candidate_objects = [schemas.CandidateCreate(name=name) for name in election_request.candidate_names]
    
    internal_election = schemas.ElectionCreate(
        title=election_request.title,
        description=election_request.description,
        # Default start time to now if not provided, though service/model might handle it.
        # But schema has optional.
        # Logic in main.py: start_time=datetime.now(timezone.utc)
        # We can set it here or in service. Service takes schemas.ElectionCreate.
        start_time=None, # Will need to be handled. main.py did it.
        end_time=election_request.end_time,
        candidates=candidate_objects
    )
    # Actually, main.py did `start_time=datetime.now(...)`.
    # Let's import datetime
    from datetime import datetime, timezone
    internal_election.start_time = datetime.now(timezone.utc)

    # We also need to schedule the start/end jobs. 
    # Clean Architecture: The service should publish an event or the controller handles the scheduler.
    # Ideally, infrastructure layer handles scheduling.
    # For this refactor, I will expose the created election and let the router (which has access to the global scheduler) add the job?
    # Or inject scheduler into Service? Injecting 'Scheduler' into Service is better.
    # But Scheduler is in main.py.
    # I will stick to main.py logic: created, then scheduler adds jobs.
    
    created_election = election_service.create_election(election_data=internal_election, user_id=current_user.id)
    
    # Returning the same response structure as before
    # Scheduler logic will be handled in main.py or we need a way to hook it.
    # I will skip the scheduler hook for a moment and address it in main.py wiring.
    
    return {"success": True, "message": "Election created and tokens distributed to all users.", "election_id": created_election.id}

@router.get("/api/elections", response_model=List[schemas.Election])
def read_elections(skip: int = 0, limit: int = 100, election_service: ElectionService = Depends(get_election_service)):
    return election_service.get_elections(skip=skip, limit=limit)

@router.get("/api/elections/{election_id}", response_model=schemas.Election)
def read_election(election_id: int, election_service: ElectionService = Depends(get_election_service)):
    db_election = election_service.get_election(election_id)
    if db_election is None:
        raise HTTPException(status_code=404, detail="Election not found")
    return db_election

@router.put("/api/elections/{election_id}", response_model=schemas.Election)
def update_election(
    election_id: int,
    election: schemas.ElectionUpdate,
    election_service: ElectionService = Depends(get_election_service),
    current_user: schemas.User = Depends(verify_admin_user),
):
    db_election = election_service.election_repo.update(election_id, election.model_dump(exclude_unset=True))
    if db_election is None:
        raise HTTPException(status_code=404, detail="Election not found")
    return db_election

@router.delete("/api/elections/{election_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_election(
    election_id: int,
    election_service: ElectionService = Depends(get_election_service),
    current_user: schemas.User = Depends(verify_admin_user),
):
    if not election_service.get_election(election_id):
        raise HTTPException(status_code=404, detail="Election not found")
    election_service.delete_election(election_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Candidates
@router.post("/elections/{election_id}/candidates", response_model=schemas.Candidate)
def create_candidate_for_election(
    election_id: int,
    candidate: schemas.CandidateCreate,
    election_service: ElectionService = Depends(get_election_service),
    # verifying manager.
    election_check = Depends(verify_election_manager)
):
    # Logic was in crud.create_candidate. Service doesn't have create_candidate exposed directly but repo has.
    # I should add create_candidate to ElectionService.
    # For now, I'll access the repo via service or add method.
    # Let's add method to Service in the previous step? Too late, file written.
    # I'll use `election_service.candidate_repo.create`.
    from src.infrastructure.database.models import Candidate
    new_candidate = Candidate(**candidate.model_dump(), election_id=election_id)
    return election_service.candidate_repo.create(new_candidate)

@router.get("/elections/{election_id}/candidates", response_model=List[schemas.Candidate])
def read_candidates_for_election(
    election_id: int, 
    election_service: ElectionService = Depends(get_election_service),
):
    return election_service.candidate_repo.get_by_election_id(election_id)

@router.put("/candidates/{candidate_id}", response_model=schemas.Candidate)
def update_candidate_details(
    candidate_id: int,
    candidate_update: schemas.CandidateUpdate,
    election_service: ElectionService = Depends(get_election_service),
    # We need a way to verify ownership. The old `verify_candidate_election_manager` dependency logic needs to be adapted or imported.
    # For now, let's implement the logic inline or use a new dependency.
    current_user: schemas.User = Depends(get_current_user)
):
    # Verify ownership
    candidate = election_service.candidate_repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    election = election_service.get_election(candidate.election_id)
    if election.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to manage this election's candidates")

    return election_service.candidate_repo.update(candidate_id, candidate_update.model_dump(exclude_unset=True))

@router.delete("/candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate_from_election(
    candidate_id: int,
    election_service: ElectionService = Depends(get_election_service),
    current_user: schemas.User = Depends(get_current_user)
):
    # Verify ownership
    candidate = election_service.candidate_repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    election = election_service.get_election(candidate.election_id)
    if election.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to manage this election's candidates")

    election_service.candidate_repo.delete(candidate_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
