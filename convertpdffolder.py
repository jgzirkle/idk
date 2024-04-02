import os
import glob
import img2pdf
import argparse

def convert_images_to_pdf(image_folder, output_pdf_path):
    # Construct the full path for PNG images in the folder
    image_paths = sorted(glob.glob(os.path.join(image_folder, "*.png")))
    
    # Check if there are images to convert
    if not image_paths:
        print("No PNG images found in the specified folder.")
        return
    
    # Convert images to PDF
    try:
        with open(output_pdf_path, "wb") as f:
            f.write(img2pdf.convert(image_paths))
        print(f"PDF created successfully at {output_pdf_path}")
    except Exception as e:
        print(f"An error occurred during the PDF creation: {e}")

if __name__ == "__main__":
    # Initialize parser
    parser = argparse.ArgumentParser(description="Convert PNG images in a folder to a single PDF file.")
    
    # Adding arguments
    parser.add_argument("image_folder", type=str, help="The folder containing PNG images to be converted to PDF.")
    parser.add_argument("output_pdf_path", type=str, help="The path to save the output PDF file.")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Call function with provided arguments
    convert_images_to_pdf(args.image_folder, args.output_pdf_path)