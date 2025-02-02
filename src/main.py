"""
Main script for real-time MIDI interaction using a pre-trained MusicVAE model.

This script initializes a MusicVAE model, opens MIDI input and output ports,
and sets up a real-time interaction loop for processing MIDI note events. It
dynamically categorizes notes into high and low ranges, generates sequences
using the model, and synchronizes playback with a metronome.
"""

from magenta.models.music_vae import TrainedModel, configs

from midi_ports import InputMidiPort, OutputMidiPort
from real_time import RealTimeInteraction

# MIDI ports
INPUT_PORTS = ["input_port"]
OUTPUT_PORTS = [
    "metronome_port",
    "high_range_reference_port",
    "low_range_reference_port",
    "high_range_generation_port",
    "low_range_generation_port",
]

# Model-related parameters
MODEL_PATH = "../models/cat-mel_2bar_big.ckpt"  # Path to the model checkpoint
MODEL_CONFIG = "cat-mel_2bar_big"  # MusicVAE configuration
BATCH_SIZE = 1  # Set to 1 for generating one sequence at a time,
# suitable for real-time interaction
MODEL_TEMPERATURE = 1.0  # Higher values increase randomness

# Timing-related attributes
BPM = 80  # Beats per minute
STEPS_PER_BEAT = 4  # Number of steps per beat (e.g., 4 for 16th notes)
SEQUENCE_LENGTH = 32  # Total number of steps in a sequence
SEQUENCE_DIMENSIONS = 2  # Dimensions of the sequence (pitch and velocity)

# Threshold-related attributes
SPLIT_PITCH_THRESHOLD = 60  # Initial pitch threshold for dividing high and
# low notes (60 = C4)
THRESHOLD_ALPHA = 0.1  # Smoothing factor for dynamic threshold adjustment


def initialize_model(model_path, batch_size, model_config):
    """
    Initializes and returns a trained MusicVAE model based on the given
    configuration and checkpoint path.

    Parameters:
        model_path (str): The file path or directory where the model's
            checkpoint is located.
        batch_size (int): The batch size to use when processing data with the
            model.
        model_config (str): A string representing the model's configuration
            name.

    Returns:
        TrainedModel: An instance of the `TrainedModel` class initialized
            with the specified configuration, batch size, and checkpoint path.
    """
    model = TrainedModel(
        configs.CONFIG_MAP[model_config],
        batch_size=batch_size,
        checkpoint_dir_or_path=model_path,
    )
    return model


def open_ports(ports, midi_port):
    """
    Opens multiple MIDI ports dynamically and returns a dictionary of opened
    ports.

    Parameters:
        ports (list of str): A list of MIDI port names to be opened.
        midi_port (MidiPort): An instance of a MIDI port handler (e.g.,
            InputMidiPort or OutputMidiPort) used to open the ports.

    Returns:
        dict: A dictionary where the keys are port names (as strings) and
            the values are the corresponding opened MIDI port objects.
    """
    ports_dict = {}

    for port_name in ports:
        # Open each port dynamically and store it in the dictionary
        ports_dict[port_name] = midi_port.open(port_name)

    return ports_dict


def open_midi_ports(input_ports, output_ports):
    """
    Opens MIDI input and output ports dynamically based on the given port
    names.

    This function takes two lists of port names, one for input ports and one
    for output ports, opens each port by name, and returns a dictionary that
    maps each port's name to the opened MIDI port object.

    Parameters:
        input_ports (list of str): A list of strings representing the names of
            MIDI input ports to be opened.
        output_ports (list of str): A list of strings representing the names
            of MIDI output ports to be opened.

    Returns:
        dict: A dictionary where the keys are port names (as strings) and
            the values are the corresponding opened MIDI port objects. The
            dictionary contains both input and output ports.
    """
    # Create instances of MIDI port handlers for input and output
    input_midi_port = InputMidiPort()
    output_midi_port = OutputMidiPort()

    # Open input ports and store them in a dictionary
    input_ports_dict = open_ports(input_ports, input_midi_port)
    # Open output ports and store them in a dictionary
    output_ports_dict = open_ports(output_ports, output_midi_port)

    # Merge input and output port dictionaries into a single dictionary
    return {**input_ports_dict, **output_ports_dict}


def main():
    """
    Main function to initialize the MusicVAE model, open MIDI ports, and
    start the real-time interaction loop.
    """
    # Initialize MusicVAE model
    model = initialize_model(MODEL_PATH, BATCH_SIZE, MODEL_CONFIG)
    print(f"Initialized model: {model}")

    # Open the MIDI ports dynamically
    midi_ports = open_midi_ports(INPUT_PORTS, OUTPUT_PORTS)

    # Print out the names and status of the opened ports
    print("\nInitialized ports:")
    for name, port in midi_ports.items():
        print(f"{name}: {port}")

    # Initialize the real-time interaction
    real_time_interaction = RealTimeInteraction(
        **midi_ports,
        model=model,
        model_temperature=MODEL_TEMPERATURE,
        bpm=BPM,
        steps_per_beat=STEPS_PER_BEAT,
        sequence_length=SEQUENCE_LENGTH,
        sequence_dimensions=SEQUENCE_DIMENSIONS,
        split_pitch_threshold=SPLIT_PITCH_THRESHOLD,
        threshold_alpha=THRESHOLD_ALPHA,
    )

    # Start the real-time interaction loop
    real_time_interaction.run()


if __name__ == "__main__":
    main()
