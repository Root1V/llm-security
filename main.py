from fastapi import FastAPI
from api.auth_routes import router
from security.credentials import load_users_from_env
import utils.logging_config

app = FastAPI(title="Architecture PE - Auth API")

app.state.users = load_users_from_env()
app.include_router(router)
