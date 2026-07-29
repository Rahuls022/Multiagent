from fastapi import FastAPI

app = FastAPI(
    title="Autonomous DevOps Swarm API",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "Autonomous DevOps Swarm Backend Running"
    }