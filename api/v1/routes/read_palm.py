import os
from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from fastapi.responses import FileResponse
import shutil
from PIL import Image
import torch
from services.palm.tools import *
from db.models.palm import *
from services.palm.rectification import *
from services.palm.detection import *
from services.palm.classification import *
from services.palm.measurement import *

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

router = APIRouter()

# Define directories
RESULTS_DIR = "./results"
INPUT_DIR = "./input"
CHECKPOINT_DIR = "./core/checkpoint/"

# Ensure directories exist
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(INPUT_DIR, exist_ok=True)

# Constants
RESIZE_VALUE = 256
PATH_TO_MODEL = os.path.join(CHECKPOINT_DIR, "checkpoint_aug_epoch70.pth")


@router.post("/process-image/")
async def process_image(file: UploadFile = File(...)):
    try:
        # Ensure directories exist
        os.makedirs(INPUT_DIR, exist_ok=True)
        os.makedirs(RESULTS_DIR, exist_ok=True)

        # Save the uploaded file
        input_file_path = os.path.join(INPUT_DIR, file.filename)
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate image
        try:
            img = Image.open(input_file_path)
            img.verify()  # Verify if the image is corrupted
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

        # Check if image is square
        img = Image.open(input_file_path)  # Re-open to access dimensions
        if img.size[0] != img.size[1]:
            raise HTTPException(status_code=400, detail="Image must be square")

        # Define result paths
        path_to_clean_image = os.path.join(RESULTS_DIR, "palm_without_background.jpg")
        path_to_warped_image = os.path.join(RESULTS_DIR, "warped_palm.jpg")
        path_to_warped_image_clean = os.path.join(RESULTS_DIR, "warped_palm_clean.jpg")
        path_to_warped_image_mini = os.path.join(RESULTS_DIR, "warped_palm_mini.jpg")
        path_to_warped_image_clean_mini = os.path.join(RESULTS_DIR, "warped_palm_clean_mini.jpg")
        path_to_palmline_image = os.path.join(RESULTS_DIR, "palm_lines.png")
        path_to_result = os.path.join(RESULTS_DIR, "result.jpg")

        # Step 0: Preprocess image
        remove_background(input_file_path, path_to_clean_image)

        # Step 1: Palm image rectification
        warp_result = warp(input_file_path, path_to_warped_image)
        if warp_result is None:
            raise HTTPException(status_code=400, detail="Warping failed")

        remove_background(path_to_warped_image, path_to_warped_image_clean)
        resize(
            path_to_warped_image,
            path_to_warped_image_clean,
            path_to_warped_image_mini,
            path_to_warped_image_clean_mini,
            RESIZE_VALUE
        )

        # Step 2: Principal line detection
        net = UNet(n_channels=3, n_classes=1)
        try:
            net.load_state_dict(torch.load(PATH_TO_MODEL, map_location=torch.device("cpu"), weights_only=True))
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="Model file not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading model: {str(e)}")

        detect(net, path_to_warped_image_clean, path_to_palmline_image, RESIZE_VALUE)

        # Step 3: Line classification
        lines = classify(path_to_palmline_image)

        # Step 4: Length measurement
        im, contents = measure(path_to_warped_image_mini, lines)

        # Step 5: Save result
        save_result(im, contents, RESIZE_VALUE, path_to_result)

        return FileResponse(path_to_result, media_type="image/jpeg", filename="result.jpg")

    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
