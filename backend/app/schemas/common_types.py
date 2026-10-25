from typing import Annotated

from pydantic import AfterValidator

from app.utils.text import clean_block, clean_line

Name = Annotated[str, AfterValidator(lambda v: clean_line(v, 2, 120, "Name"))]
Description = Annotated[str, AfterValidator(lambda v: clean_block(v, 1000, "Description"))]
Title = Annotated[str, AfterValidator(lambda v: clean_line(v, 3, 150, "Title"))]
Subject = Annotated[str, AfterValidator(lambda v: clean_line(v, 2, 100, "Subject"))]
NoteDescription = Annotated[str, AfterValidator(lambda v: clean_block(v, 2000, "Description"))]
AdminComment = Annotated[str, AfterValidator(lambda v: clean_block(v, 500, "Comment"))]
