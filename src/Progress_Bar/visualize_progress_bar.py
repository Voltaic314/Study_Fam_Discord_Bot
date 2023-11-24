'''
Author: Logan Maupin

The purpose of this module is to visualize the yearly percentage
amount in a visual display via a progress bar image.
'''

import progress_calculator
from PIL import Image, ImageDraw, ImageFont

def generate_progress_bar(progress):
    # Set the image size
    width, height = 400, 50

    # Create a white background
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Calculate the progress bar length
    progress_length = int(width * progress)

    # Draw the progress bar
    draw.rectangle([(0, 0), (progress_length, height)], fill="green")

    # Add text to show progress percentage
    font = ImageFont.load_default()
    text = f"{progress * 100:.2f}%"
    text_width, text_height = draw.textsize(text, font)
    text_position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(text_position, text, fill="black", font=font)

    # Save or display the image
    image.save("progress_bar.png")
    image.show()


def main():
    '''
    This just displays the order in which to actually run the functions
    '''
    
    current_yearly_progress = progress_calculator.get_total_yearly_percentage()
    generate_progress_bar(current_yearly_progress)


if __name__ == "__main__":
    main()
