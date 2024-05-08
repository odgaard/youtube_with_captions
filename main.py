import sys
import os
from pytube import YouTube
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip


def download_youtube_video(url, path_to_save_video):
    yt = YouTube(url)
    # Select the highest resolution video-only stream
    video_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True).order_by('resolution').desc().first()
    # Select the highest quality audio stream
    audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()

    video_filename = yt.title.replace('/', '_') + '_video.mp4'
    audio_filename = yt.title.replace('/', '_') + '_audio.m4a'

    video_path = os.path.join(path_to_save_video, video_filename)
    audio_path = os.path.join(path_to_save_video, audio_filename)

    if not os.path.exists(video_path):
        video_stream.download(output_path=path_to_save_video, filename=video_filename)
        print(f"Downloaded video to {video_path}")
    else:
        print(f"Video already exists at {video_path}")

    if not os.path.exists(audio_path):
        audio_stream.download(output_path=path_to_save_video, filename=audio_filename)
        print(f"Downloaded audio to {audio_path}")
    else:
        print(f"Audio already exists at {audio_path}")

    return video_path, audio_path

def merge_video_audio(video_path, audio_path, output_path):
    # Formulate command with proper quoting of paths
    command = f'ffmpeg -i "{video_path}" -i "{audio_path}" -c:v copy -c:a aac "{output_path}"'
    os.system(command)
    print(f"Merged video and audio into {output_path}")

def download_subtitles(url, path_to_save_subtitles):
    yt = YouTube(url)
    stream = yt.streams.first()
    captions = yt.captions
    if captions:
        for caption in captions.all():
            print(f"Language: {caption.name}, Language Code: {caption.code}")
    else:
        print("No subtitles available.")
    subtitle_stream = captions.get_by_language_code('en-US')
    if subtitle_stream:
        subtitle_srt = subtitle_stream.generate_srt_captions()
        subtitle_path = f"{path_to_save_subtitles}/{yt.title.replace('/', '_')}.srt"
        with open(subtitle_path, 'w') as f:
            f.write(subtitle_srt)
        print(f"Downloaded subtitles to {subtitle_path}")
        return subtitle_path
    else:
        print("No subtitles available.")
        return None

def srt_time_to_seconds(time_str):
    """Convert SRT time format to total seconds."""
    hours, minutes, seconds = time_str.split(':')
    seconds, milliseconds = seconds.split(',')
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
    return total_seconds


def add_subtitles_to_video(video_path, subtitle_path):
    video = VideoFileClip(video_path)
    video_width, video_height = video.size

    with open(subtitle_path, 'r') as f:
        subtitles = f.read()

    clips = [video]
    scaled_fontsize = int(round(video_height / 15))
    offset_height = video_height - int(round(video_height / 9))
    border_width = int(round(video_width / 96))
    for i, part in enumerate(subtitles.split('\n\n')):
        if part.strip():
            index, time, text = part.split('\n', 2)
            start, end = time.split(' --> ')
            start_sec = srt_time_to_seconds(start.strip())
            end_sec = srt_time_to_seconds(end.strip())
            # Ensure consistent font size and text box width
            text_clip = TextClip(text, fontsize=scaled_fontsize, color='white', font='Arial', size=(video.w - border_width, None), method='caption').set_position(('center', video_height - offset_height)).set_duration(end_sec - start_sec).set_start(start_sec)
            clips.append(text_clip)

    final_clip = CompositeVideoClip(clips)
    final_video_path = video_path.replace('.mp4', '_with_subs.mp4')
    final_clip.write_videofile(final_video_path, codec="libx264")
    print(f"Created new video with subtitles at {final_video_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <YouTube URL>")
        sys.exit(1)
    url = sys.argv[1]
    download_folder = "downloads"
    video_path, audio_path = download_youtube_video(url, download_folder)
    output_video_path = os.path.join(download_folder, 'final_output.mp4')
    merge_video_audio(video_path, audio_path, output_video_path)
    subtitle_path = download_subtitles(url, download_folder)
    if subtitle_path:
        add_subtitles_to_video(output_video_path, subtitle_path)

if __name__ == '__main__':
    main()

