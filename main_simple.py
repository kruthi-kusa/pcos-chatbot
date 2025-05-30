from fastapi import FastAPI

# Simple FastAPI app for testing
app = FastAPI(title="PCOS Health Assistant API")

@app.get("/")
def read_root():
    return {"message": "Hello from PCOS API!", "status": "working"}

@app.get("/test")
def test_endpoint():
    return {"test": "This endpoint works!", "server": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)