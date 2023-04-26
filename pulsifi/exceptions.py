"""
    Custom exceptions for use within the pulsifi app.
"""

from django.http import HttpRequest


class HttpResponseBadRequestError(Exception):
    """ Provided HTTP request resulted in a critical error. """

    DEFAULT_MESSAGE = "The provided HTTP request resulted in a critical error."

    def __init__(self, message: str = None, request: HttpRequest = None) -> None:
        self.message: str = message or self.DEFAULT_MESSAGE
        self.request = request

        super().__init__(message or self.DEFAULT_MESSAGE)

    def __str__(self) -> str:
        """
            Returns formatted message & properties of the
            HttpResponseBadRequestError.
        """

        return f"{self.message} (request={repr(self.request)})"


class GETParameterError(Exception):
    """ Provided GET parameters in HTTP request contain an invalid value. """

    DEFAULT_MESSAGE = "One or more of the supplied GET parameters have an invalid value."

    def __init__(self, message: str = None, get_parameters: dict[str, str] = None) -> None:
        self.message = message or self.DEFAULT_MESSAGE

        if get_parameters is None:
            self.get_parameters = {}
        else:
            self.get_parameters = get_parameters

        super().__init__(message or self.DEFAULT_MESSAGE)

    def __str__(self) -> str:
        """ Returns formatted message & properties of the GetParameterError. """

        return f"{self.message} (get_parameters={repr(self.get_parameters)})"


class ReportableContentTypeNamesSettingError(ValueError):
    """
        Provided REPORTABLE_CONTENT_TYPE_NAMES contains a value that is not a
        valid model name.
    """

    DEFAULT_MESSAGE = "One of the supplied REPORTABLE_CONTENT_TYPE_NAMES is not a valid model name."

    def __init__(self, message: str = None, reportable_content_type_name: str = None) -> None:
        self.message: str = message or self.DEFAULT_MESSAGE
        self.reportable_content_type_name = reportable_content_type_name

        super().__init__(message or self.DEFAULT_MESSAGE)

    def __str__(self) -> str:
        """ Returns formatted message & properties of the GetParameterError. """

        return f"{self.message} (reportable_content_type_name={repr(self.reportable_content_type_name)})"


class NotEnoughTestDataError(StopIteration):
    """
        Not enough test data values were available, to generate a value for the
        given field from the test data JSON file.
    """

    DEFAULT_MESSAGE = "Not enough test data values were available, to generate one from the test data JSON file."

    def __init__(self, message: str = None, field_name: str = None) -> None:
        self.message: str = message or self.DEFAULT_MESSAGE
        self.field_name = field_name

        super().__init__(message or self.DEFAULT_MESSAGE)

    def __str__(self) -> str:
        """
            Returns formatted message & properties of the
            NotEnoughTestDataError.
        """

        return f"{self.message} (field_name={repr(self.field_name)})"
