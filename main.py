from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers import health_controller, generator_controller, processor_controller, shared_resources
from controllers.quizzes_controller import router as quizzes_router
from controllers.document_controller import router as upload_router
from controllers.results_controller import router as results_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_controller.router)
app.include_router(generator_controller.router)
app.include_router(processor_controller.router)
app.include_router(quizzes_router, prefix="/quiz", tags=["quiz"])
app.include_router(shared_resources.router)
app.include_router(upload_router)
app.include_router(results_router, prefix="/results", tags=["results"])


@app.get("/")
async def root():
  return {"message": "Hello World"}
