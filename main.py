from fastapi import FastAPI, UploadFile, File
from convertors import split, ConvertorManager, Convertor
import pandas as pd

app = FastAPI()


@app.post("/v1/dataset/")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        return {"message": "Please upload a CSV file."}

    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        return {"message": f"Error reading CSV file: {str(e)}"}

    # TODO: add a random hash id to end of filename
    df.to_csv(f"datasets/{file.filename}", index=False)

    return {
        "id": file.filename.replace(".csv", ""),
    }


@app.get("/v1/dataset/{dataset_id}/")
def preprocess(dataset_id: str):
    datasets_splits = split(f"datasets/{dataset_id}.csv")
    for convertor_class in ConvertorManager.get_all_convertors():
        c = convertor_class(dataset_id=dataset_id, splits=datasets_splits)
        c.convert()