from fastapi import APIRouter

router = APIRouter()


@router.get("/check")
async def check():
  return {"Message": "Live"}
