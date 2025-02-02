"""
Module for managing the real-time MIDI interaction, including processing
incoming MIDI messages, managing reference and generated sequences, and
synchronizing with a metronome.
"""

import time

import numpy as np

from metronome import Metronome
from midi_player import MIDIPlayer
from sequence_generator import SequenceGenerator
from sequence_processor import SequenceProcessor


class RealTimeInteraction:
    """
    Handles real-time MIDI interaction, including processing MIDI input,
    managing reference and generated sequences, and synchronizing with a
    metronome.

    This class processes MIDI input in real-time, categorizes notes into high
    and low ranges based on a dynamic pitch threshold, and manages sequences
    for playback and generation. It also quantizes timing based on BPM.
    """

    # pylint: disable=too-many-arguments
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        input_port,
        high_range_reference_port,
        low_range_reference_port,
        high_range_generation_port,
        low_range_generation_port,
        metronome_port,
        model,
        model_temperature=1.0,
        bpm=120,
        steps_per_beat=4,
        sequence_length=32,
        sequence_dimensions=2,
        split_pitch_threshold=60,
        threshold_alpha=0.1,
    ):
        """
        Initializes the real-time MIDI interaction handler.

        Parameters:
            input_port (mido.ports.BaseInput): MIDI input port.
            high_range_reference_port (mido.ports.BaseOutput): Output port
                for high-range reference sequences.
            low_range_reference_port (mido.ports.BaseOutput): Output port for
                low-range reference sequences.
            high_range_generation_port (mido.ports.BaseOutput): Output port
                for generated high-range sequences.
            low_range_generation_port (mido.ports.BaseOutput): Output port for
                generated low-range sequences.
            metronome_port (mido.ports.BaseOutput): Output port for metronome
                click.
            model: The model used for sequence generation.
            model_temperature (float, optional): Temperature parameter for the
                model's generation. Default is 1.0.
            bpm (int, optional): Beats per minute. Default is 120.
            steps_per_beat (int, optional): Number of steps per beat. Default
                is 4.
            sequence_length (int, optional): Total number of steps in a
                sequence. Default is 32.
            sequence_dimensions (int, optional): Dimensions of the sequence.
                Default is 2, for pitch and velocity.
            split_pitch_threshold (int, optional): Initial pitch threshold
                dividing high and low notes. Default is 60 (C4).
            threshold_alpha (float, optional): Smoothing factor for split
                pitch threshold adjustment. Default is 0.1.
        """
        # MIDI ports for interaction with external devices
        self.input_port = input_port
        self.metronome_port = metronome_port
        self.high_range_reference_port = high_range_reference_port
        self.low_range_reference_port = low_range_reference_port
        self.high_range_generation_port = high_range_generation_port
        self.low_range_generation_port = low_range_generation_port

        # Model-related attributes
        self.model = model
        self.model_temperature = model_temperature

        # Timing-related attributes
        self.bpm = bpm
        self.first_step = 0
        self.steps_per_beat = steps_per_beat  # Number of steps per beat
        self.beat_duration = 60 / bpm  # Duration of a single beat in seconds
        self.quantized_step_duration = (
            self.beat_duration / self.steps_per_beat
        )  # Duration of a single step
        self.end_of_beat_step = (
            self.steps_per_beat - 1
        )  # Index of the last step in a beat
        self.sequence_length = (
            sequence_length  # Total number of steps in a sequence
        )
        self.sequence_dimensions = sequence_dimensions  # Pitch and velocity
        self.end_of_sequence_step = (
            self.sequence_length - 1
        )  # Step index for the end of the sequence

        # Threshold-related attributes
        self.split_pitch_threshold = split_pitch_threshold  # Initial threshold
        self.threshold_alpha = (
            threshold_alpha  # Smoothing factor for threshold adjustment
        )

        # Initialize sequences and related variables
        self._reset_sequence_variables()
        self.high_range_generation_sequence = []
        self.low_range_generation_sequence = []

        # Timing variables for beat and step synchronization
        self.next_quantized_step = self.start_time
        self.next_beat_time = self.start_time

        # Initialize components
        self.metronome = Metronome(
            port_name=self.metronome_port
        )  # Metronome to keep time
        self.player = MIDIPlayer()  # MIDI player for playback
        self.sequence_generator = SequenceGenerator(
            self.model
        )  # Sequence generator for MIDI sequence creation
        self.sequence_processor = SequenceProcessor(
            self.quantized_step_duration, self.sequence_length
        )  # Processor for sequence timing and manipulation

    def run(self):
        """
        Starts the real-time MIDI interaction loop.
        """
        try:
            print("\nStarting Real-Time Interaction")
            while True:
                current_time = time.time()
                self._process_midi_messages(current_time)
                self._manage_timing(current_time)

        except KeyboardInterrupt:
            print("\nExiting Real-Time Interaction...")

    def _reset_sequence_variables(self):
        """
        Resets the sequence variables to their initial state.
        """
        self.step = (
            self.first_step
        )  # Current step in the sequence, starting from 0
        self.start_time = (
            time.time()
        )  # Record the current time as the start time

        # Initialize the high and low range reference sequences
        # as zero matrices (for pitch and velocity)
        self.high_range_reference_sequence = np.zeros(
            [self.sequence_dimensions, self.sequence_length]
        )
        self.low_range_reference_sequence = np.zeros(
            [self.sequence_dimensions, self.sequence_length]
        )

    def _process_midi_messages(self, current_time):
        """Process all pending MIDI messages."""
        # Store the first midi message
        first_message = next(self.input_port.iter_pending(), None)

        # Process the MIDI message if it exists and is not
        # a clock or control change message
        if first_message and first_message.type not in [
            "clock",
            "control_change",
        ]:
            self._process_midi_message(first_message, current_time)

    def _process_midi_message(self, message, current_time):
        """
        Processes an incoming MIDI message and routes it to the correct
        output port. Updates note sequences accordingly.

        Parameters:
            message (mido.Message): The incoming MIDI message.
            current_time (float): The current timestamp.
        """

        # Define target port and sequence according to the high or
        # low range of the message note
        is_high_range = message.note >= self.split_pitch_threshold
        target_port = (
            self.high_range_reference_port
            if is_high_range
            else self.low_range_reference_port
        )
        target_sequence = (
            self.high_range_reference_sequence
            if is_high_range
            else self.low_range_reference_sequence
        )

        # Send message to the correct output port
        target_port.send(message)

        # Process the note event
        self.sequence_processor.process_note_event(
            message,
            current_time,
            target_sequence,
            self.step,
            self.next_quantized_step,
        )

        # Dynamically adjust split pitch threshold
        self.split_pitch_threshold = self._adjust_split_pitch_threshold(
            message.note
        )

    def _adjust_split_pitch_threshold(self, note_pitch):
        """
        Adjusts the split_pitch_threshold with the given note.

        Parameters:
            note_pitch (int): The note pitch.
        """
        return round(
            self.threshold_alpha * note_pitch
            + (1 - self.threshold_alpha) * self.split_pitch_threshold
        )

    def _manage_timing(self, current_time):
        """
        Manage timing for quantized steps.
        """
        # Advance step if timing applies
        if current_time >= self.next_quantized_step:
            self._advance_step()

    def _advance_step(self):
        """
        Advance the step and handle beat/sequence completion.
        """
        # Handle the end of a beat
        if self.step % self.steps_per_beat == self.end_of_beat_step:
            self._handle_beat()

        # Handle the end of a sequence
        if self.step == self.end_of_sequence_step:
            self._handle_sequence_completion()
        else:
            self.step += 1  # Advance step

        # Update the next quantized step time
        self.next_quantized_step += self.quantized_step_duration

    def _handle_beat(self):
        """
        Handle end-of-beat logic.
        """
        # Update next beat time
        self.next_beat_time += self.beat_duration

        # Send the metronome message
        self.metronome.send_message(self.step)

    def _handle_sequence_completion(self):
        """
        Handles the end of a sequence by generating and playing the
        next sequence. Resets step and sequence buffers.
        """
        # Generate sequences for both high and low ranges
        self._generate_sequence(
            self.high_range_reference_sequence,
            self.high_range_generation_sequence,
        )
        self._generate_sequence(
            self.low_range_reference_sequence,
            self.low_range_generation_sequence,
        )

        # Play generated sequences for both high and low ranges
        self._play_generated_sequence(
            self.high_range_generation_sequence,
            self.high_range_generation_port,
        )
        self._play_generated_sequence(
            self.low_range_generation_sequence, self.low_range_generation_port
        )

        # Reset sequence variables for the next loop
        self._reset_sequence_variables()

    def _generate_sequence(self, sequence, generated_sequences):
        """
        Converts a sequence into a boolean matrix and triggers async generation
        if the sequence contains any nonzero values.

        Parameters:
            sequence (np.ndarray): The reference sequence to process.
            generated_sequences (list): List to store generated sequences.
        """
        # Check if there are any stored sequence
        first_sequence = sequence[0]
        if np.any(first_sequence):

            # Convert sequence to the suitable one-hot encoding format
            # for the model
            total_midi_notes = 90
            sequence = (
                np.arange(total_midi_notes) == first_sequence[:, None]
            ).astype(bool)

            # Generate a new sequence
            self.sequence_generator.generate_async(
                sequence,
                generated_sequences,
                self.sequence_length,
                self.model_temperature,
            )

    def _play_generated_sequence(self, generated_sequences, output_port):
        """
        Plays the next available generated sequence asynchronously.

        Parameters:
            generated_sequences (list): List of generated sequences.
            output_port (mido.ports.BaseOutput): The MIDI output port to
                send the sequence to.
        """
        # Check if there are sequences in queue
        if generated_sequences:

            # Play the generated sequence and remove it from the queue
            played_sequence_idx = 0
            self.player.play_async(
                generated_sequences.pop(played_sequence_idx),
                self.bpm,
                output_port,
            )
