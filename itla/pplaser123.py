from enum import IntEnum

from .itla12 import ITLA12
from .itla_errors import *


class Mode(IntEnum):
    normal = 0
    nodither = 1
    whisper = 2


class PPLaser123(ITLA12):
    """
    The pure photonics laser class implements specific features or handles particular
    quirks of the pure photonics laser. The pure photonics laser has additional
    registers for a couple of applications.

    * `set_frequency` and `set_fcf` had to be overridden
    * `get_frequency` is *not* overridden because these registers can still be read without issue
    """

    def __init__(self, serial_port, baudrate=9600, sleep_time=0.1):
        """sets up the additional frequency max and min variables which will be set upon
        connecting to the laser. We have found that Pure Photonics lasers do not
        return the RVEError when setting the frequency out of spec.

        This sets up the additional register yaml file for pure photonics specific functions.
        """
        register_files = ["registers_pp.yaml"]

        self._frequency_max = None
        self._frequency_min = None

        super().__init__(
            serial_port, baudrate, register_files=register_files, sleep_time=sleep_time
        )

    def connect(self):
        """Overriden connect function with query for max and min frequency"""
        super().connect()
        self._frequency_max = self.get_frequency_max()
        self._frequency_min = self.get_frequency_min()

    def set_fcf(self, freq):
        """
        This sets the first channel frequency.
        It does not reset the channel so this frequency will only be equal
        to the output frequency if channel=1.

        Because the `set_frequency` function calls this function this will also
        correct the issue in setting the frequency generally.

        verifies that fcf is set within the appropriate laser frequency range
        and raises RVE error if not
        """
        if freq < self._frequency_min or freq > self._frequency_max:
            raise RVEError(
                "The desired frequency is outside " "of the range for this laser."
            )

        super().set_fcf(freq)

    def get_mode(self):
        """get which low noise mode"""

        response = self._mode()
        response = Mode(int.from_bytes(response, "big"))

        return response

    def set_mode(self, mode):
        self._mode(mode)

    def normalmode(self):
        """set mode to standard dither mode"""
        self._mode(Mode.normal)

    def nodithermode(self):
        """Set mode to nodither mode

        It is unclear whether this just also activates whisper mode.
        The feature guide says "a value of 1 defaults to 2".
        """
        self._mode(Mode.nodither)

    def whispermode(self):
        """Enables whisper mode where all control loops
        are disabled resulting in a lower noise mode."""
        self._mode(Mode.whisper)

    def cleanjump(self):
        mode = self.get_mode()
        if mode == Mode.normal:
            raise Exception(
                "Laser in normal mode. You must be in nodither"
                "or whisper mode to use cleanjump."
            )

        # transfer frequency, temperature and current to memory
        self._cjstart(1)
        # calculate filter 1
        self._cjstart(1)
        # calculate filter 1
        self._cjstart(1)
        # Execute the jump
        self._cjstart(1)

    def stop_cleanjump(self):
        self._cjstart(0)

    def set_cleanjump_frequency(self, freq):
        """
        Set the size of the jump in THz to the fourth decimal place.
        XXX.XXXX
        """
        freq_jump = str(round(freq * 1e4))
        self._cjthz(int(freq_jump[0:3]))
        self._cjghz(int(freq_jump[3:]))

    def set_cleanjump_sled(self, temperature):
        """
        temperature in C
        """
        self._cjsled(round(temperature * 1e2))

    def set_cleanjump_current(self, current):
        """
        current in mA
        """
        self._cjcurrent(round(current * 1e1))

    def get_cleanjump_offset(self):
        response = self._cjoffset()
        return (int.from_bytes(response, "big", signed=True) - 10000) * 0.1
