from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from fastapi_pagination import add_pagination
from app.utils.logger import logger as log
from app.api.routes import router as api_router
from app.messaging import getQueryValidator
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel

import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    log.info("START API CONNECT TO {}".format(settings.DGT_CONNECT))
    connection = getQueryValidator()
    connection.connect()
    
    #ml_models["answer_to_everything"] = fake_answer_to_everything_ml_model
    yield
    # Clean up the ML models and release the resources
    #ml_models.clear()
    log.info("STOP")
    connection.disconnect()

def create_app() -> FastAPI:
    #oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    if False:
        oauth2_flows = OAuthFlowsModel(password={"tokenUrl": "token", "scopes": {}})
        openapi = lambda: {"info": {"title": settings.PROJECT_NAME, "version": "1.0"}, 
                           "security": [{"OAuth2PasswordBearerWithCookie": oauth2_flows.dict()}],
                           "openapi": "3.1.0"
                           }
    #oauth2_flows = OAuthFlows()
    app = FastAPI(title=settings.PROJECT_NAME,version=settings.VERSION,
                  docs_url=settings.PROJECT_DOCS,
                  openapi_url=f"{settings.API_PREFIX}/openapi.json",
                  #swagger_ui_oauth2_redirect_url="/api/docs/oauth2-redirect",
                  lifespan=lifespan
                  )
    
    #app.openapi = openapi
    add_pagination(app)
    app.include_router(api_router, prefix=settings.API_PREFIX)
    
    return app


app = create_app()
@app.middleware("http")
async def log_requests(request, call_next):
    log.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    log.info(f"reply: {response.status_code}")
    return response


def wrap_main():
    try:
        uvicorn.run(app, host="0.0.0.0", port=settings.API)
    except KeyboardInterrupt:  
        log.info(f'Ask stop API {settings.VERSION} ')




if __name__ == "__main__":
    wrap_main()
