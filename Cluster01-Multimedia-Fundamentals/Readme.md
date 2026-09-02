# Experiment 1: Image Analyzer

## 1. Problem Statement

Develop a Python-based Image Analyzer that accepts an image file path and generates a metadata report containing basic image properties and available EXIF metadata.

The analyzer should support common multimedia image formats such as JPG, JPEG, PNG and optionally TIFF, WEBP and BMP.

---

## 2. Objectives

- Analyze image file properties programmatically.
- Identify the image format and file size.
- Extract image width and height.
- Determine image resolution and color mode.
- Extract available EXIF metadata.
- Handle invalid files and unsupported formats.
- Implement the solution using modular and reusable functions.

---

## 3. Technologies Used

- Python 3
- Pillow (PIL Fork)
- Operating System: Windows
- IDE: Visual Studio Code

---

## 4. Supported Formats

### Required

- JPG
- JPEG
- PNG

### Bonus

- TIFF
- WEBP
- BMP

---

## 5. Approach / Methodology

1. Accept the image path through the command line.
2. Check whether the specified file exists.
3. Validate the image file extension.
4. Open the image using the Pillow library.
5. Extract basic image metadata.
6. Extract available EXIF metadata.
7. Convert metadata into a readable format.
8. Display the final metadata report.
9. Handle errors gracefully.

---

## 6. Algorithm / Workflow

```text
Start
  |
  v
Accept Image Path
  |
  v
Check File Exists?
  |
  +---- No ----> Display Error
  |
 Yes
  |
  v
Check Supported Format
  |
  +---- No ----> Display Unsupported Format Error
  |
 Yes
  |
  v
Open Image using Pillow
  |
  v
Extract Basic Metadata
  |
  v
Extract EXIF Metadata
  |
  v
Format Metadata
  |
  v
Display Image Metadata Report
  |
  v
End