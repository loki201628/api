<<<<<<< HEAD
# from fastapi import FastAPI
# from core.services.contact_services import router as contact_router
#
# app = FastAPI(title="Contact Management System")
#
# # Include Contact Management Routes
# app.include_router(contact_router)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8080)

#2.

# from fastapi import FastAPI
# from core.services.contact_services import router as contact_router
# from core.services.postgres_services import router as activity_router
#
# app = FastAPI(title="Contact Management System")
#
# # Include Contact Management Routes
# app.include_router(contact_router)
#
# # Include Activity Tracking Routes
# app.include_router(activity_router)
#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8080)

#3.

from fastapi import FastAPI
from core.services.contact_services import router as contact_router
from core.services.postgres_services import router as activity_router
from core.services.relationship_services import router as relationship_router
from core.services.report_services import router as report_router

app = FastAPI(title="Contact Management System")

# Include Contact Management Routes
app.include_router(contact_router)

# Include Activity Tracking Routes
app.include_router(activity_router)

# Include Contact Relationship Routes
app.include_router(relationship_router)

# Include Report Routes
app.include_router(report_router)
=======

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}

@app.get("/greet/{name}")
def greet_user(name: str):
    return {"greeting": f"Hello, {name}!"}
>>>>>>> 8d3ed4208c879d0c97f32d9bad92b13cb1d4a101
