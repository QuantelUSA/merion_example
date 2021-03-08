# !Python3
"""
This module contains examples of how to communicate with a Quantel Merion C laser
over a network connection.
"""

import logging
from telnetlib import Telnet
from typing import Optional

SEND_PACKET = b'\r\n'
RECV_PACKET = b'\r> '

class CommunicateQlic:
    """
    Class for handling communications with a MerionC laser over a
    TCP/IP socket connection.
    """
    PORT_NUMBER = 10001
    TIMEOUT = 5

    def __init__(self, ipaddr: str, portnum: int = PORT_NUMBER) -> None:
        """
        Initialize the class

        Args:
            ipaddr (str): ip address of the laser
            portnum (int): socket port number
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
            logging.error(f'Could not find system at {self._port_num}')

        except ConnectionRefusedError:
            logging.error(f'Connection refused on port {self._port_num}')

        return result
    #end def


    def close_connection(self):
        """
        Closes the socket connection to the laser.
        """
        if self._connection:
            self._connection.close()
    #end def


    def send_qlic_command(
            self,
            command: str, tree: str, branch: str, function: str,
            parameter: str = '', value: str = ''
        ) -> None:
        """
        Send a command to the laser

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
            cmd_str = f'{command} /{tree}/{branch}/{function} {parameter}'
        elif value:
            # set /tree/branch/function value
            cmd_str = f'{command} /{tree}/{branch}/{function} {value}'
        else:
            # get
            cmd_str = f'{command} /{tree}/{branch}/{function}'

        assert self._connection
        self._connection.write(cmd_str.encode())
        self._connection.write(SEND_PACKET)
    #end def


    def send_alias_command(self, alias: str, value: str = '') -> None:
        """
        Send a simple command to the laser.

        Args:
            alias (str): short-cut command
            value (str, optional): parameter value. Defaults to ''.
        """
        if value:
            cmd_str = f'{alias} {value}'
        else:
            cmd_str = f'{alias}'

        assert self._connection  # make sure we have a connection
        self._connection.write(cmd_str.encode())
        self._connection.write(SEND_PACKET)
    #end def


    def read_qlic_response(self) -> Optional[str]:
        """
        Get a response from the laser.

        Returns:
            Optional[str]: laser response, or None.
        """
        assert self._connection  # make sure we have a connection
        response = self._connection.read_until(RECV_PACKET, timeout=self.TIMEOUT)
        if response:
            return response.decode()
        else:
            return None
    #end def
#end class


class MerionCLaser:
    """
    Simple class for controlling a Merion C laser over a socket
    connection.
    """
    def __init__(self, ipaddr: str) -> None:
        self.ip_addr = ipaddr
        self._qlic_comm = CommunicateQlic(ipaddr)
        self.state = 0
    #end def

    def get_current_state(self) -> int:
        self._qlic_comm.send_alias_command('state')
        resp = self._qlic_comm.read_qlic_response()
        if resp:
            return int(resp, 16)
        else:
            return -1
    #end def


    def open_connection(self) -> bool:
        return self._qlic_comm.open_connection()
    #end def


    def set_dpw_to_max(self):
        self._qlic_comm.send_qlic_command('propget', 'osc', 'diode', 'cpw', 'limitmax')
        dpw_max = self._qlic_comm.read_qlic_response()
        if dpw_max:
            self._qlic_comm.send_qlic_command('set', 'osc', 'diode', 'cpw', dpw_max)
    #end def
#end class
