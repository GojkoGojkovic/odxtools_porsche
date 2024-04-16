# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .exceptions import EncodeError, odxraise


@dataclass
class EncodeState:
    """Utility class to holding the state variables needed for encoding a message.
    """

    #: payload that has been constructed so far
    coded_message: bytearray

    #: a mapping from short name to value for each parameter
    parameter_values: Dict[str, Any]

    #: The absolute position in bytes from the beginning of the PDU to
    #: which relative positions refer to, e.g., the beginning of the
    #: structure.
    origin_byte_position: int

    #: The absolute position in bytes from the beginning of the PDU
    #: where the next object ought to be placed into the PDU
    cursor_byte_position: int

    #: The bit position [0-7] where the next object ought to be
    #: placed into the PDU
    cursor_bit_position: int

    #: If encoding a response: request that triggered the response
    triggering_request: Optional[bytes] = None

    #: Mapping from the short name of a length-key parameter to bit
    #: lengths (specified by LengthKeyParameter)
    length_keys: Dict[str, int] = field(default_factory=dict)

    #: Mapping from the short name of a table-key parameter to the
    #: short name of the corresponding row of the table (specified by
    #: TableKeyParameter)
    table_keys: Dict[str, str] = field(default_factory=dict)

    #: The cursor position where a given length- or table key is located
    #: in the PDU
    key_pos: Dict[str, int] = field(default_factory=dict)

    #: Flag whether we are currently the last parameter of the PDU
    #: (needed for MinMaxLengthType, EndOfPduField, etc.)
    is_end_of_pdu: bool = True

    def emplace_atomic_value(self, new_data: bytes, param_name: str) -> None:
        pos = self.cursor_byte_position

        # Make blob longer if necessary
        min_length = pos + len(new_data)
        if len(self.coded_message) < min_length:
            self.coded_message.extend([0] * (min_length - len(self.coded_message)))

        for i in range(len(new_data)):
            # insert new byte. this is pretty hacky: it will fail if
            # the value to be inserted is bitwise "disjoint" from the
            # value which is already in the PDU...
            if self.coded_message[pos + i] & new_data[i] != 0:
                odxraise(
                    f"Object '{param_name}' overlaps with another parameter (bits are already set)",
                    EncodeError,
                )
            self.coded_message[pos + i] |= new_data[i]

        self.cursor_byte_position += len(new_data)
        self.cursor_bit_position = 0
