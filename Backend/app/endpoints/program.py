
from fastapi import APIRouter, Depends, status

from app.controllers.program_controller import (
    create_program,
    list_programs,
    update_program,
    delete_program,
)
from app.controllers.auth_controller import require_admin
from app.schemas.academic import ProgramCreate, ProgramUpdate

program = APIRouter(prefix="/programs", tags=["Programs"])


@program.post("/", status_code=status.HTTP_201_CREATED)
async def create(data: ProgramCreate, admin=Depends(require_admin)):
    return await create_program(data)


@program.get("/")
async def get_all(admin=Depends(require_admin)):
    return await list_programs()


@program.patch("/{program_id}")
async def update(
    program_id: str,
    data: ProgramUpdate,
    admin=Depends(require_admin),
):
    return await update_program(program_id, data)


@program.delete("/{program_id}")
async def delete(program_id: str, admin=Depends(require_admin)):
    return await delete_program(program_id)
