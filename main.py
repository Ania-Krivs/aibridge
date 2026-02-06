from fastapi import FastAPI
from data.db import Base
from data.db import engine
from routers import projectConfig, user, admin


app = FastAPI(
    title=projectConfig.__projname__,
    version=projectConfig.__version__,
    description=projectConfig.__description__
    )

Base.metadata.create_all(bind=engine)

app.include_router(admin.router)
app.include_router(user.router)
