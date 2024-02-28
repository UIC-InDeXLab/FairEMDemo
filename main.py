import os

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from convertors import split, ConvertorManager, Convertor
from utils import load_dataset_as_df
import pandas as pd

load_dotenv()

app = FastAPI()


@app.post("/v1/datasets/")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        return {"message": "Please upload a CSV file."}

    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        return {"message": f"Error reading CSV file: {str(e)}"}

    # TODO: add a random hash id to end of filename
    df.to_csv(os.path.join(os.getenv("DATASET_UPLOAD_PATH", "./datasets"), file.filename), index=False)

    return {
        "id": file.filename.replace(".csv", ""),
    }


@app.get("/v1/datasets/{dataset_id}/preprocess/")
def preprocess(dataset_id: str):
    datasets_splits = split(load_dataset_as_df(dataset_id))
    for convertor_class in ConvertorManager.get_all_convertors():
        c: Convertor = convertor_class(dataset_id=dataset_id, splits=datasets_splits)
        c.convert()


@app.get("/v1/datasets/{dataset_id}/match/")
def match(dataset_id: str, matcher: str, matching_threshold: float = 0.5, fairness_threshold: float = 0.2):
    pass
