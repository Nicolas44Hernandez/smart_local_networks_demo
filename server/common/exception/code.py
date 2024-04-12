""" Server errors """

from enum import Enum


class ErrorCode(Enum):
    """Enumerate which gather all data about possible errors"""

    # Please enrich this enumeration in order to handle other kind of errors
    UNEXPECTED_ERROR = (0, 500, "Unexpected error occurs")
    TELNET_CONNECTION_ERROR = (1, 500, "Error in Telnet connection")
    TELNET_COMMANDS_FILE_ERROR = (2, 500, "Error in telnet commands load, check commands file")
    TELNET_COMMAND_NOT_FOUND = (3, 500, "Telnet command not found, check config")
    UNKNOWN_BAND_WIFI = (4, 400, "Wifi band doesnt exist")
    ERROR_IN_PREDICTOR_MODEL_LOAD = (5, 500, "Error in 5GHZ ON/OFF rtt predictor model load")
    
    # pylint: disable=unused-argument
    def __new__(cls, *args, **kwds):
        """Custom new in order to initialize properties"""
        obj = object.__new__(cls)
        obj._value_ = args[0]
        obj._http_code_ = args[1]
        obj._message_ = args[2]
        return obj

    @property
    def http_code(self):
        """The http code corresponding to the error"""
        return self._http_code_

    @property
    def message(self):
        """The message corresponding to the error"""
        return self._message_
