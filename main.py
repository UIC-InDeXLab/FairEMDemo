import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from websockets import ConnectionClosed

from convertors import split, ConvertorManager, Convertor
from matchers import MatcherManager, Matcher
from utils import load_dataset_as_df
import pandas as pd

load_dotenv()


def startup():
    Path(os.getenv("DATASET_UPLOAD_PATH", "./datasets")).mkdir(parents=True, exist_ok=True)


app = FastAPI(on_startup=[startup])
active_clients = set()


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
    return {"successful": True}


@app.get("/v1/datasets/{dataset_id}/match/")
async def match(dataset_id: str, matcher: str, matching_threshold: float = 0.5, fairness_threshold: float = 0.2,
                epochs: int = 1):
    manager: MatcherManager = MatcherManager.instance()
    matcher_class: Matcher = manager.get_matcher(matcher)
    matcher = matcher_class(dataset_id=dataset_id, matching_threshold=matching_threshold, epochs=epochs)
    matcher.match()
    return {"successful": True}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        await websocket.send_text("Connection established!")

        while True:
            msg = await websocket.receive_text()
            if msg.lower() == "close":
                await websocket.close()
                break
            elif msg.lower().startswith("dataset_id="):
                print(f'CLIENT says - {msg}')
                websocket.dataset_id = msg.lower().replace("dataset_id=", "")
                active_clients.add(websocket)
                # await websocket.send_text(f"Your message was: {msg}")

    except (WebSocketDisconnect, ConnectionClosed):
        print("Client disconnected")
