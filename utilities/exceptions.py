from werkzeug.exceptions import HTTPException
from werkzeug.utils import escape
from werkzeug.wrappers import Response
from werkzeug._compat import text_type

NOT_YET_AVAILABLE_ERROR = 403
INTEGRITY_ERROR = 408
VALIDATION_FAILED = 409
ACTION_REQUIRED = 209


class CustomException(HTTPException):
    def __init__(self, code, data=None, description=None, name=None):
        """
        custom model for handling HTTPExceptions
        :param code: Response Code
        :param description: Description of error
        """
        super(CustomException, self).__init__(code)
        self.code = code
        self.response_name = name
        self.description = description

        if data:
            self.data = data

    def get_description(self, environ=None):
        """Get the description."""
        return u'<p>Description: %s</p>' % escape(self.description)

    def get_body(self, environ=None):
        """Get the HTML body."""
        return text_type((
            u'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
            u'<title>%(code)s %(name)s</title>\n'
            u'<h1>%(name)s</h1>\n'
            u'%(description)s\n'
        ) % {
            'code':         self.code,
            'name':         escape(self.response_name),
            'description':  self.get_description()
        })

    def get_response(self, environ=None):
        """
        Update HTTPException response processing
        :param environ:
        :return:
        """
        if self.response is not None:
            return self.response
        headers = self.get_headers()
        return Response(self.get_body(environ), self.code, headers)


class ValidationFailed(HTTPException):
    """
    *34* `Validation Failed`
    Custom exception thrown when form validation fails.
    This is only useful when making REST api calls
    """

    name = "Validation Failed"
    code = VALIDATION_FAILED
    description = (
        '<p>Validation Failed</p>'
    )

    def __init__(self, data):
        """
        :param: data: A dictionary containing the field errors that occured
        :param: description: Optional description to send through
        """
        super(ValidationFailed, self).__init__()
        self.data = data
        self.status= 409

    # def get_response(self, environment):
    #     resp = super(ValidationFailed, self).get_response(environment)
    #     resp.status = "%s %s"(self.code, self.name.upper())
    #     return resp


class FurtherActionException(HTTPException):
    """
    *34* `Further Action Exception`
    Custom exception thrown when further action is required by the user.
    This is only useful when making REST api calls
    """

    name = "Further Action Required"
    code = ACTION_REQUIRED
    description = (
        '<p>Further Action Required</p>'
    )

    def __init__(self, data, description=None):
        """
        :param: data: A dictionary containing the field errors that occured
        :param: description: Optional description to send through
        """
        HTTPException.__init__(self)
        self.description = description
        self.data = data

    def get_response(self, environment=None):
        resp = super(FurtherActionException, self).get_response(environment)
        resp.status = "%s %s" % (self.code, self.name.upper())
        return resp


# other exceptions to implement
# not found exception, also raised by the service layer
# authentication failed. This would be raised whenever authentication fails
# permission denied. The would occur when a user attempts to access unauthorized content


class IntegrityException(HTTPException):
    """
    *32* `Integrity Exception`
    Custom exception thrown when an attempt to save a resource fails.
    This is only useful when making REST api calls
    """

    name = "Integrity Exception"
    code = INTEGRITY_ERROR
    description = (
        '<p>Integrity Exception</p>'
    )

    def __init__(self, e):
        """
        param: e: parent exception to wrap and manipulate
        """
        HTTPException.__init__(self)
        self.data = e.data if hasattr(e, "data") else {}
        self.code = e.code if hasattr(e, "code") else INTEGRITY_ERROR
        bits = e.message.split("\n")
        if len(bits) > 1:
            self.data["error"] = bits[0]
            self.data["message"] = " ".join(bits[1:]).strip()
        else:
            self.data["message"] = " ".join(bits).strip()

    def get_response(self, environment=None):
        resp = super(IntegrityException, self).get_response(environment)
        resp.status = "%s %s" %(self.code, self.name.upper())
        return resp


class ObjectNotFoundException(Exception):
    """ This exception is thrown when an object is queried by ID and not retrieved """

    def __init__(self, klass, obj_id):
        message = "%s: Object not found with id: %s" % (klass.__name__, obj_id)
        self.data = {"name": "ObjectNotFoundException", "message": message}
        self.status = 501
        super(ObjectNotFoundException, self).__init__(message)


class ActionDeniedException(Exception):
    """ This exception is thrown when an object is queried by ID and not retrieved """

    def __init__(self, klass, obj_id):
        message = "%s: Action denied on object id: %s" % (klass.__name__, obj_id)
        self.data = {"name": "ActionDeniedException", "message": message}
        self.status = 40
        super(ActionDeniedException, self).__init__(message)
