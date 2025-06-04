#!/usr/bin/env python3
"""
Generate simple test images with geometric shapes for vision testing
"""

from PIL import Image, ImageDraw
import os
from pathlib import Path

def create_test_images_dir():
    """Create test images directory"""
    test_images_dir = Path("tests/test_images")
    test_images_dir.mkdir(exist_ok=True)
    return test_images_dir

def create_circle_image(color: str, size: tuple = (200, 200)) -> Image.Image:
    """Create an image with a colored circle"""
    img = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw circle in the center
    margin = 30
    draw.ellipse([margin, margin, size[0]-margin, size[1]-margin], fill=color)
    
    return img

def create_triangle_image(color: str, size: tuple = (200, 200)) -> Image.Image:
    """Create an image with a colored triangle"""
    img = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw triangle (equilateral)
    center_x, center_y = size[0] // 2, size[1] // 2
    radius = 70
    
    # Calculate triangle points
    points = [
        (center_x, center_y - radius),  # Top point
        (center_x - radius * 0.866, center_y + radius * 0.5),  # Bottom left
        (center_x + radius * 0.866, center_y + radius * 0.5),  # Bottom right
    ]
    
    draw.polygon(points, fill=color)
    
    return img

def create_rectangle_image(color: str, size: tuple = (200, 200)) -> Image.Image:
    """Create an image with a colored rectangle"""
    img = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw rectangle in the center
    margin = 40
    draw.rectangle([margin, margin, size[0]-margin, size[1]-margin], fill=color)
    
    return img

def create_square_image(color: str, size: tuple = (200, 200)) -> Image.Image:
    """Create an image with a colored square"""
    img = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw square in the center
    side = 120
    center_x, center_y = size[0] // 2, size[1] // 2
    x1 = center_x - side // 2
    y1 = center_y - side // 2
    x2 = center_x + side // 2
    y2 = center_y + side // 2
    
    draw.rectangle([x1, y1, x2, y2], fill=color)
    
    return img

def create_mixed_shapes_image(size: tuple = (300, 200)) -> Image.Image:
    """Create an image with multiple shapes"""
    img = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(img)
    
    # Red circle on the left
    draw.ellipse([20, 60, 80, 120], fill='red')
    
    # Blue triangle in the middle
    center_x, center_y = 150, 100
    radius = 40
    points = [
        (center_x, center_y - radius),
        (center_x - radius * 0.866, center_y + radius * 0.5),
        (center_x + radius * 0.866, center_y + radius * 0.5),
    ]
    draw.polygon(points, fill='blue')
    
    # Green square on the right
    draw.rectangle([220, 60, 280, 120], fill='green')
    
    return img

def main():
    """Generate all test images"""
    test_dir = create_test_images_dir()
    
    # Colors to test
    colors = {
        'red': '#FF0000',
        'blue': '#0000FF', 
        'green': '#00FF00',
        'yellow': '#FFFF00',
        'purple': '#800080',
        'orange': '#FFA500'
    }
    
    # Shapes to test
    shapes = {
        'circle': create_circle_image,
        'triangle': create_triangle_image,
        'rectangle': create_rectangle_image,
        'square': create_square_image
    }
    
    print("🎨 Generating test images...")
    
    # Generate individual shape images
    for color_name, color_value in colors.items():
        for shape_name, shape_func in shapes.items():
            filename = f"{color_name}_{shape_name}.png"
            filepath = test_dir / filename
            
            img = shape_func(color_value)
            img.save(filepath)
            print(f"✅ Created {filename}")
    
    # Generate mixed shapes image
    mixed_img = create_mixed_shapes_image()
    mixed_path = test_dir / "mixed_shapes.png"
    mixed_img.save(mixed_path)
    print(f"✅ Created mixed_shapes.png")
    
    # Generate a simple black and white pattern
    pattern_img = Image.new('RGB', (200, 200), 'white')
    draw = ImageDraw.Draw(pattern_img)
    
    # Checkerboard pattern
    square_size = 25
    for i in range(0, 200, square_size * 2):
        for j in range(0, 200, square_size * 2):
            draw.rectangle([i, j, i + square_size, j + square_size], fill='black')
            draw.rectangle([i + square_size, j + square_size, i + square_size * 2, j + square_size * 2], fill='black')
    
    pattern_path = test_dir / "checkerboard_pattern.png"
    pattern_img.save(pattern_path)
    print(f"✅ Created checkerboard_pattern.png")
    
    print(f"\n🎯 All test images saved to: {test_dir}")
    print(f"📊 Total images created: {len(list(test_dir.glob('*.png')))}")

if __name__ == "__main__":
    main() 