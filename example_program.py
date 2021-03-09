# !Python3
"""
This module contains examples of how to communicate with a Quantel Merion C laser
over a network connection.

A few things to be aware of:
* All data is read/written to/from the socket as bytes, so if a command is built
as a string type, it will need to be converted to bytes before sending it. Just use
the str.encode() method to do this.
"""

import logging
from telnetlib import Telnet
from typing import Optional


class MerionLaserConnection:
    """
    Class for handling communications with a MerionC laser over a
    TCP/IP socket connection.
    """
    PORT_NUMBER = 10001
    TIMEOUT = 5
    SEND_PACKET_TERMINATOR = b'\r\n'  # sent at end of each command
    READ_PACKET_TERMINATOR = b'\n> '  # laser sends this at end of a response


    def __init__(self, ipaddr: str, portnum: int = PORT_NUMBER) -> None:
        """
        Initialize the class

        Args:
            ipaddr (str): ip address of the laser
            portnum (int): socket port number, defaults to 10001
        """
        self._ip_addr = ipaddr
        self._port_num = portnum
        self._connection: Optional[Telnet] = None
    #end def


    def open_connection(self) -> bool:
        """
        Open a socket (telnet) connection

        Returns:
            bool: True if successful
        """
        result = False

        try:
            self._connection = Telnet(host=self._ip_addr, port=self._port_num, timeout=self.TIMEOUT)
            result = True

        except TimeoutError:
            logging.error(f'Could not find laser at {self._port_num}')

        except ConnectionRefusedError:
            logging.error(f'Connection refused on port {self._port_num}')

        return result
    #end def


    def close_connection(self):
        """
        Closes the socket connection to the laser.
        """
        if self._connection is not None:
            self._connection.close()
    #end def


    def send_command_to_laser(
            self,
            command: str, tree: str, branch: str, function: str,
            parameter: str = '', value: str = ''
        ) -> bool:
        """
        Sends a command to the laser.

        Args:
            command (str): base command
            tree (str): command tree
            branch (str): command branch
            function (str): function
            parameter (str, optional): optional parameter value. Defaults to ''.
            value (str, optional): optional value. Defaults to ''.
        """
        if parameter:
            # this will manipulate a property: propget /tree/branch/function parameter
            cmd_str = f'{command} /{tree}/{branch}/{function} {parameter}'.encode()
        elif value:
            # set /tree/branch/function value
            cmd_str = f'{command} /{tree}/{branch}/{function} {value}'.encode()
        else:
            # get
            cmd_str = f'{command} /{tree}/{branch}/{function}'.encode()

        assert self._connection, 'Socket connection to laser must be open'

        # send the command to laser over socket connection
        try:
            self._connection.write(cmd_str + self.SEND_PACKET_TERMINATOR)
            return True

        except Exception as err:
            logging.exception(err)
            return False
    #end def


    def send_alias_command_to_laser(self, alias: str, value: str = '') -> bool:
        """
        Send a simple (alias) command to the laser. Alias (or "shortcut") commands
        are simple one-word commands.

        Args:
            alias (str): short-cut command
            value (str, optional): parameter value. Defaults to ''.
        """
        if value:
            cmd_str = f'{alias} {value}'.encode()
        else:
            cmd_str = f'{alias}'.encode()

        assert self._connection, 'Socket connection to laser must be open'

        try:
            # send command
            self._connection.write(cmd_str + self.SEND_PACKET_TERMINATOR)
            return True

        except Exception as err:
            logging.exception(err)
            return False
    #end def


    def read_response(self) -> Optional[str]:
        """
        Get a response from the laser.

        Returns:
            Optional[str]: laser response, or None.
        """
        assert self._connection, 'Socket connection to laser must be open'

        # check for a response
        response = self._connection.read_until(self.READ_PACKET_TERMINATOR, timeout=self.TIMEOUT)
        if response:
            # get part of response before the terminator
            result, *_ = response.partition(self.READ_PACKET_TERMINATOR)
        else:
            result = None

        # decode response and strip off extraneous characters
        return result.decode().strip() if result else None
    #end def
#end class


class MerionCLaser:
    """
    Simple class for controlling a Merion C laser over a socket
    connection.
    """
    def __init__(self, connection: MerionLaserConnection) -> None:
        """
        Init the class.

        Args:
            ipaddr (str): ip address of the laser.
            portnum (int): socket port number, defaults to 10001.
        """
        self._connection = connection
    #end def


    def get_current_state(self) -> int:
        """
        Query the laser to get current state bits.

        Returns:
            int: the state value as a 16bit integer.
        """
        self._connection.send_alias_command_to_laser('state')
        resp = self._connection.read_response()
        if resp:
            return int(resp, 16)
        else:
            return -1
    #end def


    def open_connection(self) -> bool:
        """
        Tries to open a socket connection to the laser.

        Returns:
            bool: True if successful
        """
        return self._connection.open_connection()
    #end def


    def set_dpw_to_max(self):
        """
        Sets the diode pulse width to its max value. This is just an example of
        how to communicate with the laser to get or set a value.
        """
        # query the laser for its max diode pulse width
        self._connection.send_command_to_laser('propget', 'osc', 'diode', 'cpw', 'limitmax')
        dpw_max = self._connection.read_response()

        # if query was successful, set the diode pulse width to the max value
        if dpw_max:
            self._connection.send_command_to_laser('set', 'osc', 'diode', 'cpw', dpw_max)
    #end def
#end class


if __name__ == '__main__':
    """
    Ask user for laser IP address and try doing some simple operations.
    """
    ip_addr = input('Enter the IP address of the laser (e.g. 192.168.10.100) -> ')
    laser = MerionCLaser(MerionLaserConnection(ip_addr))

    print('Connecting to laser...')
    if laser.open_connection():
        print('Connected to laser')

        print('Setting diode pulse width to max...')
        laser.set_dpw_to_max()

        print('Getting laser state...')
        print(f'Laser state (hex) = {laser.get_current_state():04X}')
    else:
        print('Connection to laser failed')
#end if
