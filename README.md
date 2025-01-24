# Description

This project allows you to download images from a private source on **CoralNet**.

## Annotations

Downloading annotations via the script is not always functional due to CoralNet server latencies.  
To obtain the annotations, please download them directly from the CoralNet website.

## Configuration (`config.yaml`)

Before running the script, ensure you complete the `config.yaml` file with the following information:

- **`username`**: Your CoralNet username.
- **`password`**: Your CoralNet password.
- **`binary_location`**: Path to the ChromeDriver binary file (optional, if necessary).
- **`nb_source`**: Identifier of the source you wish to download from.
- **`nb_images_download`**: Number of images to download.

Example `config.yaml` file in the repository. 

## Installing Dependencies

To install the required dependencies, run the following command:
```python
pip install -r requirements.txt
```
## Downloading Images

To start the image download, run the following command:
```bash
pyhon3 main.py
```

