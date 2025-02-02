"""
Module for sending MIDI messages to a specified output port to simulate
a metronome. It distinguishes between different types of beats (e.g., first
beat of a sequence, first beat of a measure, and regular beats) and sends
appropriate MIDI messages for each step.
"""

import mido


class Metronome:
    """
    A MIDI-based metronome that sends beat messages to a specified MIDI port.

    This metronome differentiates between the first beat of the sequence,
    the first beat of a measure, and regular beats, sending corresponding
    MIDI messages.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, port_name, steps_per_sequence=32, steps_per_measure=16):
        """
        Initializes the Metronome.

        Parameters:
            port_name (str): Name of the MIDI output port to which metronome
            messages will be sent.
            steps_per_sequence (int, optional): Total number of steps in a
                sequence. Default is 32.
            steps_per_measure (int, optional): Number of steps in a measure.
                Default is 16.
        """
        self.metronome_port = port_name
        self.steps_per_sequence = steps_per_sequence
        self.steps_per_measure = steps_per_measure

        # Define note values for different beats
        self.first_beat_of_sequence_note = 64
        self.first_beat_of_measure_note = 62
        self.regular_beat_note = 60
        self.velocity = 100

    def send_message(self, step):
        """
        Determines the type of beat (first beat of the sequence, first beat
        of a measure, or regular beat) based on the current step and sends
        the corresponding MIDI message to the metronome's output port.

        Parameters:
            step (int): Current step in the sequence (0-indexed).
        """
        # Determine the note based on the step
        if step == self.steps_per_sequence - 1:  # First sequence beat
            note = self.first_beat_of_sequence_note
        elif step % (self.steps_per_measure - 1) == 0:  # First measure beat
            note = self.first_beat_of_measure_note
        else:  # Regular beat
            note = self.regular_beat_note

        # Send the MIDI message to the output port
        self.metronome_port.send(
            mido.Message("note_on", note=note, velocity=self.velocity)
        )
