"""
Module for handling MIDI input and output ports using the mido library.
This module includes functionality for retrieving available input/output
ports and opening connections to those ports for communication.
"""

from abc import ABC, abstractmethod

import mido


class MidiPort(ABC):
    """
    Abstract base class for MIDI ports.

    This class defines the common interface for listing and opening MIDI ports.
    """

    @abstractmethod
    def list_ports(self):
        """
        Lists available MIDI ports.

        Returns:
            list of str: A list of available MIDI port names.
        """

    @abstractmethod
    def open_selected_port(self, port_name):
        """
        Opens the selected MIDI port.

        Parameters:
            port_name (str): The name of the MIDI port to open.

        Returns:
            The opened MIDI port object.
        """

    def _select_and_open(self, port_name):
        """
        Lists available MIDI ports, prompts the user to select one by number,
        and opens the selected port. If no ports are available or the selection
        is invalid, it falls back to opening a default port.

        Parameters:
            port_name (str): The name of the MIDI port type

        Returns:
            The opened MIDI port object, or None if no ports are available.
        """
        available_devices = self.list_ports()
        if not available_devices:
            print(f"\nNo available {port_name} devices.")
            return None

        print(f"\nAvailable {port_name} devices:")
        for idx, device in enumerate(available_devices):
            print(f"{idx + 1}: {device}")

        try:
            selected = (
                int(input(f"\nSelect |{port_name}| device by number: ")) - 1
            )
            if 0 <= selected < len(available_devices):
                return self.open_selected_port(available_devices[selected])
            raise ValueError("Invalid selection")
        except (ValueError, IndexError):
            print("\nInvalid selection. Using default MIDI port.")
            return self.open_selected_port(None)


class InputMidiPort(MidiPort):
    """
    Handles MIDI input ports.
    """

    def list_ports(self):
        """
        Lists available MIDI input ports.

        Returns:
            list of str: A list of available MIDI input port names.
        """
        # pylint: disable=no-member
        return mido.get_input_names()

    def open_selected_port(self, port_name):
        """
        Opens a MIDI input port.

        Parameters:
            port_name (str): The name of the MIDI input port to open.

        Returns:
            mido.ports.BaseInput: The opened MIDI input port object.
        """
        # pylint: disable=no-member
        return mido.open_input(port_name)

    def open(self, port_name):
        """
        Allows the user to select and open a MIDI input port by name.

        Parameters:
            port_name (str): The name of the MIDI input port type.

        Returns:
            mido.ports.BaseInput: The opened MIDI input port object.
        """
        return self._select_and_open(port_name)


class OutputMidiPort(MidiPort):
    """
    Handles MIDI output ports.
    """

    def list_ports(self):
        """
        Lists available MIDI output ports.

        Returns:
            list of str: A list of available MIDI output port names.
        """
        # pylint: disable=no-member
        return mido.get_output_names()

    def open_selected_port(self, port_name):
        """
        Opens a MIDI output port.

        Parameters:
            port_name (str): The name of the MIDI output port to open.

        Returns:
            mido.ports.BaseOutput: The opened MIDI output port object.
        """
        # pylint: disable=no-member
        return mido.open_output(port_name)

    def open(self, port_name):
        """
        Allows the user to select and open a MIDI output port by name.

        Parameters:
            port_name (str): The name of the MIDI output port type.

        Returns:
            mido.ports.BaseOutput: The opened MIDI output port object.
        """
        return self._select_and_open(port_name)
