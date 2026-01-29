"""FastAPI main application."""

from fastapi import FastAPI

app = FastAPI(title="Patient Management API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Patient Management API"}


# TODO: Add patient endpoints here
