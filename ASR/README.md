# ASR API Project

This project provides a simple API for automatic speech recognition (ASR) using a TensorFlow Lite model.

## Setup for Local Development (Windows)

This setup is for running the server directly on your local machine for development and testing.

1.  **Install FFmpeg:**
    This project requires FFmpeg for audio format conversion. Please follow a guide to install it on Windows and ensure it is added to your system's PATH. You can verify the installation by opening a new terminal and running `ffmpeg -version`.

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```
    Activate the environment: `venv\\Scripts\\activate`

3.  **Install development dependencies:**
    ```bash
    pip install -r requirements.dev.txt
    ```

4.  **Configure the environment:**
    Create a `.env` file in the project root. Copy `.env.example` and set the `MODEL_PATH` to the correct path of your `.tflite` model. For example:
    ```
    MODEL_PATH=E:/workspace/cursor/ASR/wav2vec2_quantized.tflite
    ```

5.  **Running the Application:**
    Run the following command from the project root:
    ```bash
    python -m src.main
    ```
    The server will start on `http://127.0.0.1:8000`.

## API Documentation (Swagger UI)

Once the server is running, access the interactive API documentation at:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

You can use this interface to test the `/transcribe/` endpoint.

## Deployment with Docker (Production)

This is the recommended way to deploy the application, especially on Linux-based systems like the RK3562.

### Prerequisites

*   Docker installed on your machine.

### Building the Docker Image

From the project root directory, run the following command. This will build an image named `asr-api`:

```bash
docker build -t asr-api .
```

### Running the Docker Container

Once the image is built, you can run it as a container:

```bash
docker run -d -p 8000:8000 --name asr-container asr-api
```
*   `-d`: Runs the container in detached mode (in the background).
*   `-p 8000:8000`: Maps port 8000 of your host machine to port 8000 of the container.
*   `--name asr-container`: Gives the container a memorable name.

The API will now be accessible at `http://<your-docker-host-ip>:8000`. On your local machine, this will be `http://127.0.0.1:8000`. 