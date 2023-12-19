#!/usr/bin/env python3
"""
specZXplay.py
Make sure Python is installed on your machine, along with the numpy and simpleaudio libraries.
"""
import numpy as np
import simpleaudio as sa
import os
import sys
import time


def get_terminal_size():
    rows, columns = os.popen('stty size', 'r').read().split()
    #print("Rows, cols: ", rows, columns)
    #time.sleep(1)  # Adjust the speed of scrolling
    return int(rows), int(columns)

def initialize_buffer(rows, columns):
    return [[' ' for _ in range(columns)] for _ in range(rows)]

def update_buffer(buffer, byte, palette, width):
    color = palette[byte % len(palette)]
    new_line = [color + ' ' * width + "\033[0m"]  # Create a new colored line
    buffer.pop(0)  # Remove the top line
    buffer.append(new_line)  # Add the new line at the bottom

def display_buffer(buffer):
    # os.system('clear' if os.name == 'posix' else 'cls')
    for row in buffer:
        print(''.join(row))
    sys.stdout.flush()


def byte_to_freq_v2(byte):
    # Map byte value (0-255) directly to frequency (0-25500 Hz)
    return byte * 100  # 0 will be 0 Hz (silence)

def display_byte(byte):
    # Display the byte in a printable format (e.g., hexadecimal)
    print(f"{byte:02x}", end="", flush=True)


def calculate_duration(bpm):
    # Calculate the duration of each tone based on BPM
    beats_per_second = bpm / 60
    return 1 / beats_per_second

def file_to_audio_v6(file_path, bpm):
    try:
        # Read file as binary
        with open(file_path, "rb") as file:
            file_bytes = file.read()

        # Convert bytes to frequencies
        frequencies = [byte_to_freq_v2(byte) for byte in file_bytes]

        # Calculate duration based on BPM

        duration_per_tone = calculate_duration(bpm)

        # Generate audio signal
        sample_rate = 16000  # Set sample rate to 16 kHz
        audio_signal = np.concatenate([
            np.sin(2 * np.pi * freq * np.linspace(0, duration_per_tone, int(sample_rate * duration_per_tone))) if freq != 0 else np.zeros(int(sample_rate * duration_per_tone))
            for freq in frequencies])

        # Normalize to 8-bit range (0-255)
        audio_signal = (audio_signal - np.min(audio_signal)) / (np.max(audio_signal) - np.min(audio_signal))  # Normalize to 0-1 range
        audio_signal = (audio_signal * 255).astype(np.uint8)  # Scale to 8-bit range and convert to unsigned 8-bit integer

        # Initialize terminal buffer
        rows, columns = get_terminal_size()
        buffer = initialize_buffer(rows, columns)
        spectrum_palette = ["\033[40m", "\033[44m", "\033[42m", "\033[46m", "\033[41m", "\033[45m", "\033[43m", "\033[47m"]

        previous_byte = None
        for byte in file_bytes:
            visualize_byte_spectrum_style(byte)  # Visualize the byte

            update_buffer(buffer, byte, spectrum_palette, columns-1)
            display_buffer(buffer)

            if byte != previous_byte:
                frequency = byte_to_freq_v2(byte)
                wave = generate_square_wave(frequency, duration_per_tone, sample_rate)
                # Normalize and convert wave to 8-bit
                wave = (wave - np.min(wave)) / (np.max(wave) - np.min(wave))  # Normalize to 0-1 range
                wave = (wave * 255).astype(np.uint8)  # Scale to 8-bit range
                previous_byte = byte

            play_obj = sa.play_buffer(wave, 1, 2, sample_rate)
            # Optionally wait for the sound to finish: 
            play_obj.wait_done()

    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def generate_square_wave(frequency, duration, sample_rate):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sign(np.sin(2 * np.pi * frequency * t))
    return wave



def estimate_audio_duration_with_repeats(file_path, bpm):
    with open(file_path, "rb") as file:
        file_bytes = file.read()

    duration_per_tone = calculate_duration(bpm)  # Duration of each tone
    total_duration = 0
    previous_byte = None

    for byte in file_bytes:
        if byte == previous_byte:
            # If the byte is the same as the previous one, double the duration
            total_duration += duration_per_tone * 2
        else:
            total_duration += duration_per_tone
            previous_byte = byte

    return total_duration


def format_duration(seconds):
    # Convert seconds to minutes and seconds for display
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes} minutes and {seconds} seconds"


def visualize_byte_spectrum_style(byte, width=80):
    """
    Visualize a byte as a colored line in the terminal using ZX Spectrum palette.
    The height of the line is determined by the number of times the byte value can be divided
    by the number of colors in the palette.
    """
    # ZX Spectrum palette (approximated to ANSI colors)
    spectrum_colors = [
        "\033[40m",  # Black
        "\033[44m",  # Blue
        "\033[42m",  # Green
        "\033[46m",  # Cyan
        "\033[41m",  # Red
        "\033[45m",  # Magenta
        "\033[43m",  # Yellow
        "\033[47m"   # White
    ]

    # Calculate color and height
    num_colors = len(spectrum_colors)
    color_index = byte % num_colors
    height = byte // num_colors

    # Generate the colored line
    color = spectrum_colors[color_index]
    line = color + " " * width + "\033[0m"  # Reset color at the end

    # Print the line 'height' times
    for _ in range(height + 1):  # Adding 1 to ensure at least one line is printed
        print(line)


# Example usage with a BPM constant
BPM = 100 # 133.7  # Beats per minute, adjust as needed
BPM *= 10  # Fix speed up

# Call file_to_audio_v3 with the file path and BPM
if len(sys.argv) < 2:
    print("Usage: python script.py <file_path>")
else:
    file_path = sys.argv[1]
    estimated_duration = estimate_audio_duration_with_repeats(file_path, BPM)
    formatted_duration = format_duration(estimated_duration)
    print(f"Estimated audio duration: {formatted_duration}")
    time.sleep(1.3) 

    file_to_audio_v6(file_path, BPM)

