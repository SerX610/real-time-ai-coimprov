"""
Module for processing MIDI note events (note-on and note-off) and updating a
sequence based on quantized steps. It handles the timing and placement of
notes within the sequence, ensuring they align with the quantized grid.
"""

import numpy as np


class SequenceProcessor:
    """
    Processes MIDI note events and organizes them into a quantized sequence.

    This class handles incoming MIDI note-on and note-off events, ensuring
    they are correctly processed and stored in the appropriate quantized
    step within a sequence.
    """

    # pylint: disable=too-many-arguments
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes
    def __init__(self, quantized_step_duration, sequence_length=32):
        """
        Initializes the SequenceProcessor.

        Parameters:
            quantized_step_duration (float): Duration of each quantized step
                in the sequence.
            sequence_length (int, optional): Total number of steps in the
                sequence. Default is 32.
        """
        # Step duration parameters
        self.quantized_step_duration = quantized_step_duration
        self.half_quantized_step_duration = 0.5 * self.quantized_step_duration

        # Sequence structure
        self.sequence_length = sequence_length
        self.first_step = 0
        self.last_step = self.sequence_length - 1

        # Adjust based on MIDI/keyboard mapping
        self.midi_pitch_adjustment = 19

        # Indexing for pitch and velocity
        self.pitch_idx = 0
        self.velocity_idx = 1

        # Note event types
        self.note_on_pitch = 0
        self.note_off_pitch = 1
        self.arbitrary_velocity = 0

    def process_note_event(
        self, message, current_time, sequence, step, next_quantized_step
    ):
        """
        Processes a note event (either note-on or note-off) and updates
        the sequence.

        Parameters:
            message (mido.Message): The MIDI message (note-on or note-off).
            current_time (float): Current time in the sequence.
            sequence (list): The sequence to update.
            step (int): Current step in the sequence.
            next_quantized_step (float): Time of the next quantized step.
        """
        # Process note-on and note-off events separately
        if (
            message.type == "note_on"
            and message.velocity > self.arbitrary_velocity
        ):  # Note-on event
            self._process_note_on(
                message, current_time, sequence, step, next_quantized_step
            )
        elif message.type == "note_off" or (
            message.type == "note_on"
            and message.velocity == self.arbitrary_velocity
        ):  # Note-off event
            self._process_note_off(
                message, current_time, sequence, step, next_quantized_step
            )

    def _process_note_on(
        self, message, current_time, sequence, step, next_quantized_step
    ):
        """
        Processes a note-on event and updates the sequence.

        Parameters:
            message (mido.Message): The note-on message.
            current_time (float): Current time in the sequence.
            sequence (list): The sequence to update.
            step (int): Current step in the sequence.
            next_quantized_step (float): Time of the next quantized step.
        """
        # Overwrite the existing note in the current step if the new
        # one has a higher velocity
        if message.velocity > self._get_velocity(sequence, step):
            nearest_step = self._get_nearest_step(
                step, current_time, next_quantized_step
            )
            self._store_note_on(message, sequence, nearest_step)

    def _store_note_on(self, message, sequence, step):
        """
        Determines the appropriate step to store the note and applies
        placeholders accordingly.

        Parameters:
            message (mido.Message): The note-on message.
            sequence (list): The sequence to update.
            step (int): The step at which the note should be stored.
        """
        # Adjust pitch using MIDI adjustment
        note_pitch = message.note - self.midi_pitch_adjustment

        # Get the velocity of the note-on event
        velocity = message.velocity

        # Store note-on event in the nearest step
        self._store_note_with_placeholder(sequence, step, note_pitch, velocity)

    def _store_note_with_placeholder(
        self, sequence, step, note_pitch, velocity
    ):
        """
        Stores a note at the given step and marks the next step as a
        note-on placeholder.

        Parameters:
            sequence (list): The sequence to update.
            step (int): The step at which the note should be stored.
            note_pitch (int): The pitch of the note.
            velocity (int): The velocity of the note.
        """
        # Placeholder offset (next step)
        note_on_placeholder_offset = 1

        # Store the note at the current step if it exists
        if step <= self.last_step:
            self._set_note(sequence, step, note_pitch, velocity)

        # Store the note-on placeholder in the next step if it exists
        if step + note_on_placeholder_offset <= self.last_step:
            self._set_note(
                sequence,
                step + note_on_placeholder_offset,
                self.note_on_pitch,
                self.arbitrary_velocity,
            )

    def _process_note_off(
        self, message, current_time, sequence, step, next_quantized_step
    ):
        """
        Processes a note-off event and updates the sequence.

        Parameters:
            message (mido.Message): The note-off message.
            current_time (float): Current time in the sequence.
            sequence (list): The sequence to update.
            step (int): Current step in the sequence.
            next_quantized_step (float): Time of the next quantized step.
        """
        # Adjust pitch using MIDI adjustment
        note_pitch = message.note - self.midi_pitch_adjustment

        # Get the current step pitch
        current_step_pitch = self._get_pitch(sequence, step)

        # Process empty and non-empty steps separately
        if (
            step != self.first_step
            and current_step_pitch == self.note_on_pitch
        ):  # Empty step
            self._process_empty_step(
                note_pitch, current_time, sequence, step, next_quantized_step
            )
        elif (
            step != self.last_step and current_step_pitch > self.note_off_pitch
        ):  # Non-empty step
            self._process_non_empty_step(
                note_pitch, current_time, sequence, step, next_quantized_step
            )

    def _process_empty_step(
        self, note_pitch, current_time, sequence, step, next_quantized_step
    ):
        """
        Processes a note-off event in an empty step.

        Parameters:
            note_pitch (int): Pitch of the note-off event.
            current_time (float): Current time in the sequence.
            sequence (list): The sequence to update.
            step (int): Current step in the sequence.
            next_quantized_step (float): Time of the next quantized step.
        """

        # Store the note-off event with its corresponding note-on event
        if not np.any(sequence[self.pitch_idx]):  # Empty sequence
            self._store_note_with_placeholder(
                sequence, self.first_step, note_pitch, self.arbitrary_velocity
            )  # First step
            self._store_note_off_in_nearest_step(
                sequence, step, current_time, next_quantized_step
            )
        else:  # Non-empty sequence
            self._find_and_store_note_off(
                note_pitch, current_time, sequence, step, next_quantized_step
            )

    def _process_non_empty_step(
        self, note_pitch, current_time, sequence, step, next_quantized_step
    ):
        """
        Processes a note-off event in a non-empty step.

        Parameters:
            note_pitch (int): Pitch of the note-off event.
            current_time (float): Current time in the sequence.
            sequence (list): The sequence to update.
            step (int): Current step in the sequence.
            next_quantized_step (float): Time of the next quantized step.
        """
        # Store the note-off in the next step if the current step is the
        # nearest one and the pitch matches the note in the current step.
        if note_pitch == self._get_pitch(sequence, step):
            self._store_note_off_in_nearest_step(
                sequence, step, current_time, next_quantized_step
            )

    def _store_note_off_in_nearest_step(
        self, sequence, step, current_time, next_quantized_step
    ):
        """
        Stores the note-off event in the nearest appropriate step.

        Parameters:
            sequence (list): The sequence to update.
            step (int): Current step in the sequence.
            current_time (float): Current time in the sequence.
            next_quantized_step (float): Time of the next quantized step.
        """
        # Define the two following steps
        next_step = step + 1
        second_next_step = next_step + 1

        # Define the target step according to the nearest quantized step
        target_step = (
            next_step
            if self._current_step_is_the_nearest_one(
                current_time, next_quantized_step
            )
            else second_next_step
        )

        # Store the note-off event
        self._store_note_off(sequence, target_step)

    def _store_note_off(self, sequence, step):
        """
        Stores the note-off message in the nearest quantized step.

        Parameters:
            sequence (list): The sequence to update.
            step (int): Current step in the sequence.
        """
        # Store the note-off event in the given step if it exists
        if step <= self.last_step:
            self._set_note(
                sequence, step, self.note_off_pitch, self.arbitrary_velocity
            )

    def _find_and_store_note_off(
        self, note_pitch, current_time, sequence, step, next_quantized_step
    ):
        """
        Finds the corresponding note-on message and stores the note-off
        message.

        Parameters:
            note_pitch (int): Pitch of the note-off event.
            current_time (float): Current time in the sequence.
            sequence (list): The sequence to update.
            step (int): Current step in the sequence.
            next_quantized_step (float): Time of the next quantized step.
        """
        # Iterate through the steps backwardly
        for idx in reversed(range(step)):
            idx_step_pitch = self._get_pitch(
                sequence, idx
            )  # Get the pitch of the step at index idx

            # Store the note-off event in the nearest step if pitches match
            if idx_step_pitch == note_pitch:
                self._store_note_off_in_nearest_step(
                    sequence, step, current_time, next_quantized_step
                )
                break

            # Stop if a previous note with a different pitch is found
            if idx_step_pitch != self.note_on_pitch:
                break

    def _get_nearest_step(self, step, current_time, next_quantized_step):
        """
        Determines the nearest quantized step based on the current time.

        Parameters:
            step (int): Current step in the sequence.
            current_time (float): Current time in the sequence.
            next_quantized_step (float): Time of the next quantized step.

        Returns:
            int: The nearest step (either the current step or the next one).
        """
        # Define next_step
        next_step = step + 1

        # Get the nearest step
        return (
            step
            if self._current_step_is_the_nearest_one(
                current_time, next_quantized_step
            )
            else next_step
        )

    def _current_step_is_the_nearest_one(
        self, current_time, next_quantized_step
    ):
        """
        Checks if the current step is the nearest one based on the
        current time.

        Parameters:
            current_time (float): Current time in the sequence.
            next_quantized_step (float): Time of the next quantized step.

        Returns:
            bool: True if the current step is the nearest one, False otherwise.
        """
        return (
            current_time
            <= next_quantized_step - self.half_quantized_step_duration
        )

    def _get_pitch(self, sequence, step):
        """
        Gets the pitch at a specific step in the sequence.

        Parameters:
            sequence (list): The sequence.
            step (int): The step index.

        Returns:
            int: The pitch value.
        """
        return sequence[self.pitch_idx][step]

    def _get_velocity(self, sequence, step):
        """
        Gets the velocity at a specific step in the sequence.

        Parameters:
            sequence (list): The sequence.
            step (int): The step index.

        Returns:
            int: The velocity value.
        """
        return sequence[self.velocity_idx][step]

    def _set_note(self, sequence, step, pitch, velocity):
        """
        Sets the pitch and velocity at a specific step in the sequence.

        Parameters:
            sequence (list): The sequence.
            step (int): The step index.
            pitch (int): The pitch value.
            velocity (int): The velocity value.
        """
        sequence[self.pitch_idx][step] = pitch
        sequence[self.velocity_idx][step] = velocity
