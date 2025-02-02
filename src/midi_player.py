"""
Module for playing generated MIDI sequences in real-time.

This module provides a MIDIPlayer class that can send MIDI note events
to an output port, playing a generated sequence either synchronously
or asynchronously. It supports tempo adjustments and handles anacrusis
(delayed start) for proper synchronization.
"""

import threading
import time

import mido


class MIDIPlayer:
    """
    A class for playing generated MIDI sequences via a MIDI output port.

    This class sends MIDI note-on and note-off messages to a specified
    MIDI output port, ensuring correct timing based on the provided BPM.
    It supports both synchronous and asynchronous playback.
    """

    def __init__(self):
        """
        Initialize the MIDIPlayer.
        """

    def play(self, generated_sequence, bpm, output_port):
        """
        Play the generated MIDI sequence.

        Parameters:
            generated_sequence (pretty_midi.PrettyMIDI): The generated MIDI
                sequence.
            bpm (int): Beats per minute, determining playback speed.
            output_port (mido.ports.BaseOutput): The MIDI output port to
                send the sequence to.
        """
        # Get the notes from the generated sequence
        midi_notes = generated_sequence.instruments[0].notes

        # Handle anacrusis (if the first note starts later than 0)
        seconds_per_beat = 60 / bpm
        anacrusis_duration = midi_notes[0].start * seconds_per_beat
        time.sleep(anacrusis_duration)

        # Play each note in the sequence
        for note in midi_notes:

            # Compute note duration in seconds based on beats per note
            note_beats = note.end - note.start
            note_duration = note_beats * seconds_per_beat

            # Define the note-on and note-off MIDI messages
            note_on_message = mido.Message(
                "note_on", note=note.pitch, velocity=note.velocity
            )
            note_off_message = mido.Message(
                "note_off", note=note.pitch, velocity=0
            )

            # Send the note-on message and then send the note-off message
            # after the corresponding note duration
            output_port.send(note_on_message)
            time.sleep(note_duration)  # Wait for the note to play
            output_port.send(note_off_message)

    def play_async(self, generated_sequence, bpm, output_port):
        """
        Play the generated MIDI sequence asynchronously.

        Parameters:
            generated_sequence (pretty_midi.PrettyMIDI): The generated MIDI
                sequence.
            bpm (int): Beats per minute, determining playback speed.
            output_port (mido.ports.BaseOutput): The MIDI output port to
                send the sequence to.
        """
        threading.Thread(
            target=self.play, args=(generated_sequence, bpm, output_port)
        ).start()
