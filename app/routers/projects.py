from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, database

router = APIRouter(prefix="/projects", tags=["Projects"])


def clean_text(value: str) -> str:
    """Utility function to clean unwanted newlines/spaces."""
    if not value:
        return value
    return value.strip().replace("\n", "").replace("\r", "")


def clean_project(project: models.Project) -> schemas.Project:
    """Return a cleaned project schema."""
    return schemas.Project(
        id=project.id,
        name=clean_text(project.name),
        location=clean_text(project.location)
    )


@router.post("/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(database.get_db)):
    db_project = models.Project(
        name=clean_text(project.name),
        location=clean_text(project.location)
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return clean_project(db_project)


@router.get("/", response_model=list[schemas.Project])
def get_projects(db: Session = Depends(database.get_db)):
    projects = db.query(models.Project).all()
    return [clean_project(p) for p in projects]


@router.get("/{project_id}", response_model=schemas.Project)
def get_project(project_id: int, db: Session = Depends(database.get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return clean_project(project)


@router.put("/{project_id}", response_model=schemas.Project)
def update_project(project_id: int, project: schemas.ProjectCreate, db: Session = Depends(database.get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_project.name = clean_text(project.name)
    db_project.location = clean_text(project.location)

    db.commit()
    db.refresh(db_project)
    return clean_project(db_project)


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(database.get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": f"Project {project_id} deleted successfully"}
