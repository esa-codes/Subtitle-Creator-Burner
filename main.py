# main.py

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import SubtitleGUI

def main():
    app = QApplication(sys.argv)
    window = SubtitleGUI()
    window.show()
    sys.exit(app.exec())

def create_subtitles(video_path, output_folder, language='en'):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get the video filename without extension
    video_filename = os.path.basename(video_path)
    video_name = os.path.splitext(video_filename)[0]
    
    # Define the output SRT file path
    srt_path = os.path.join(output_folder, f"{video_name}.srt")
    
    print(f"Creating subtitles for {video_path}")
    print(f"Output SRT will be saved to: {srt_path}")
    
    # Create subtitles using Whisper
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    
    # Write the subtitles to SRT file
    with open(srt_path, "w", encoding="utf-8") as srt_file:
        write_srt(result["segments"], file=srt_file)
    
    print(f"Subtitles created successfully at {srt_path}")
    
    # Verify the file exists before returning
    if not os.path.exists(srt_path):
        print(f"ERROR: SRT file was not created at {srt_path}")
        return None
        
    return srt_path

def burn_subtitles(video_path, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get the video filename without extension
    video_filename = os.path.basename(video_path)
    video_name = os.path.splitext(video_filename)[0]
    
    # Create subtitles
    subtitles_path = create_subtitles(video_path, output_folder)
    
    if not subtitles_path or not os.path.exists(subtitles_path):
        print(f"Error: Subtitle file not found at {subtitles_path}")
        return
    
    # Define the output video path
    output_video_path = os.path.join(output_folder, f"{video_name}_with_subs.mp4")
    
    # Burn subtitles using FFmpeg
    print(f"Burning subtitles into video...")
    subprocess.run([
        "ffmpeg", "-i", video_path, 
        "-vf", f"subtitles={subtitles_path}", 
        "-c:a", "copy", 
        output_video_path
    ])
    
    print(f"Video with subtitles created at {output_video_path}")

if __name__ == "__main__":
    main()
