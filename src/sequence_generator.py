"""
Module for encoding input sequences and generating new sequences by sampling
from a learned latent space using a model, and decoding them into MIDI format.
It includes both synchronous and asynchronous generation methods.
"""

import threading

import note_seq
import numpy as np


class SequenceGenerator:
    """
    A class for generating MIDI sequences using a Variational Autoencoder
    model.

    This class encodes input sequences into a latent representation,
    samples from the latent space, and decodes the samples back into MIDI
    sequences. It also supports scaling sequences and asynchronous generation.
    """

    def __init__(self, model):
        """
        Initialize the SequenceGenerator.

        Parameters:
            model: The model used for encoding and decoding sequences.
        """
        self.model = model

    def _scale_sequence(self, sequence, scaling_factor=2):
        """
        Scales the timing of the notes in a given sequence by a specified
        scaling factor.

        Parameters:
            sequence (NoteSequence): The sequence to be scaled.
            scaling_factor (float, optional): The factor by which to scale
                the sequence. Default is 2.

        Returns:
            sequence (NoteSequence): The scaled sequence.
        """
        # Scale the start and end times of each note in the sequence
        for note in sequence.notes:
            note.start_time *= scaling_factor
            note.end_time *= scaling_factor

        # Adjust the total duration of the sequence
        sequence.total_time *= scaling_factor

        return sequence

    def generate(
        self,
        input_sequence,
        generated_sequences,
        sequence_length=32,
        temperature=1.0,
    ):
        """
        Generate a new sequence based on the input sequence.

        Parameters:
            input_sequence (np.ndarray): The input sequence to encode.
            generated_sequences (list): List to store the generated sequences.
            sequence_length (int, optional): Length of the generated sequence.
                Default is 32.
            temperature (float, optional): Temperature parameter for sampling.
                Default is 1.0.
        """
        # Encode the input sequence to get mu (mean) and
        # sigma (standard deviation)
        _, mu, sigma = self.model.encode_tensors(
            [input_sequence], [sequence_length]
        )

        # Generate a new sample z
        epsilon = np.random.normal(size=len(mu[0]))
        z = mu + sigma * epsilon

        # Decode the generated sequence
        decoded_sequence = self.model.decode(
            length=sequence_length, z=z, temperature=temperature
        )[0]

        # Scale the decoded sequence to represent 2 bars
        scaling_factor = 2
        scaled_sequence = self._scale_sequence(
            decoded_sequence, scaling_factor
        )

        # Convert the sequence to the suitable MIDI format and store it
        generated_midi_sequence = note_seq.note_sequence_to_pretty_midi(
            scaled_sequence
        )
        generated_sequences.append(generated_midi_sequence)

    def generate_async(
        self,
        input_sequence,
        generated_sequences,
        sequence_length=32,
        temperature=1.0,
    ):
        """
        Generate a new sequence asynchronously.

        Parameters:
            input_sequence (np.ndarray): The input sequence to encode.
            generated_sequences (list): List to store the generated sequences.
            sequence_length (int, optional): Length of the generated sequence.
                Default is 32.
            temperature (float, optional): Temperature parameter for sampling.
                Default is 1.0.
        """
        threading.Thread(
            target=self.generate,
            args=(
                input_sequence,
                generated_sequences,
                sequence_length,
                temperature,
            ),
        ).start()
