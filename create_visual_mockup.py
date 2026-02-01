#!/usr/bin/env python3
"""
Visual mockup showing what the creation mode overlay looks like.
This creates a simple demonstration image showing the visual feedback.
"""

import cv2
import numpy as np


def create_mockup():
    """Create a mockup image showing the visual feedback."""
    
    # Create a sample frame (640x480)
    width, height = 640, 480
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add a gradient background to make it look more realistic
    for y in range(height):
        intensity = int(40 + (y / height) * 60)
        frame[y, :] = [intensity, intensity, intensity]
    
    # Add some fake "video content" - a grid
    for x in range(0, width, 80):
        cv2.line(frame, (x, 0), (x, height), (60, 60, 60), 1)
    for y in range(0, height, 60):
        cv2.line(frame, (0, y), (width, y), (60, 60, 60), 1)
    
    # Define example points in percentage, then convert to pixels
    points_pct = [
        [25.0, 30.0],  # First point (will be green)
        [55.0, 25.0],  # Second point
        [65.0, 50.0],  # Third point
        [50.0, 70.0],  # Fourth point
        [30.0, 55.0],  # Fifth point
    ]
    
    # Convert to pixel coordinates
    pixel_points = []
    for point in points_pct:
        px = int(width * point[0] / 100)
        py = int(height * point[1] / 100)
        pixel_points.append((px, py))
    
    # Draw the visual feedback (same as _draw_creation_overlay)
    
    # Draw lines connecting the points
    for i in range(len(pixel_points) - 1):
        cv2.line(frame, pixel_points[i], pixel_points[i + 1], (0, 255, 255), 2)
    
    # Draw closure line (thinner)
    cv2.line(frame, pixel_points[-1], pixel_points[0], (0, 255, 255), 1)
    
    # Draw circles at each point
    for i, point in enumerate(pixel_points):
        if i == 0:
            # First point - green
            cv2.circle(frame, point, 8, (0, 255, 0), -1)
            cv2.circle(frame, point, 8, (255, 255, 255), 2)
        else:
            # Other points - yellow
            cv2.circle(frame, point, 6, (0, 255, 255), -1)
            cv2.circle(frame, point, 6, (255, 255, 255), 2)
    
    # Add labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, "CREATION MODE - Visual Feedback Demo", (10, 30), 
                font, 0.7, (255, 255, 255), 2)
    
    # Add legend
    legend_y = 420
    cv2.circle(frame, (30, legend_y), 8, (0, 255, 0), -1)
    cv2.circle(frame, (30, legend_y), 8, (255, 255, 255), 2)
    cv2.putText(frame, "First point (start)", (50, legend_y + 5), 
                font, 0.5, (255, 255, 255), 1)
    
    cv2.circle(frame, (30, legend_y + 30), 6, (0, 255, 255), -1)
    cv2.circle(frame, (30, legend_y + 30), 6, (255, 255, 255), 2)
    cv2.putText(frame, "Subsequent points", (50, legend_y + 35), 
                font, 0.5, (255, 255, 255), 1)
    
    # Add point coordinates
    for i, (point, point_pct) in enumerate(zip(pixel_points, points_pct)):
        coord_text = f"[{point_pct[0]:.1f}, {point_pct[1]:.1f}]"
        offset_x = 15 if i > 0 else 15
        offset_y = -15 if i % 2 == 0 else 20
        cv2.putText(frame, coord_text, (point[0] + offset_x, point[1] + offset_y), 
                    font, 0.4, (255, 255, 255), 1)
    
    return frame


def main():
    """Generate and save the mockup."""
    print("Creating visual feedback mockup...")
    
    frame = create_mockup()
    
    # Save the image
    output_path = "creation_mode_mockup.png"
    cv2.imwrite(output_path, frame)
    print(f"✓ Mockup saved to {output_path}")
    
    # Also display it if running in an environment with display
    try:
        cv2.imshow("Creation Mode Visual Feedback", frame)
        print("\nPress any key to close the preview window...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except:
        print("(Display not available - image saved to file)")
    
    print("\nThis demonstrates what users will see when creating triggers:")
    print("- Green circle at the first point (8px radius)")
    print("- Yellow circles at subsequent points (6px radius)")
    print("- Yellow lines connecting all points (2px thick)")
    print("- Thin closure line from last to first (1px thick)")


if __name__ == '__main__':
    main()
