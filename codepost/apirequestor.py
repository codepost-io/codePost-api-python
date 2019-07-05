# =============================================================================
# codePost v2.0 SDK
#
# HTTP CLIENT SUB-MODULE
# =============================================================================

from __future__ import print_function # Python 2

# Python stdlib imports
import copy as _copy
import functools as _functools
import inspect as _inspect
import json as _json
import logging as _logging
import os as _os
import platform as _platform
import threading as _threading
import time as _time
import uuid as _uuid
import sys as _sys
try:
    # Python 3
    from urllib.parse import urljoin
    from urllib.parse import quote as urlquote
    from urllib.parse import urlencode as urlencode
except ImportError: # pragma: no cover
    # Python 2
    from urlparse import urljoin
    from urllib import quote as urlquote
    from urllib import urlencode as urlencode

# External dependencies
import better_exceptions as _better_exceptions
import requests as _requests

# Local imports
import codepost

from codepost import __version__ as _CODEPOST_SDK_VERSION
from codepost import httpclient as _httpclient

from .util import config as _config
from .util import logging as _logging

from .util.misc import _make_f

# =============================================================================

# Replacement f"..." compatible with Python 2 and 3
_f = _make_f(globals=lambda: globals(), locals=lambda: locals())

# =============================================================================

# Global submodule constants
_LOG_SCOPE = "{}".format(__name__)

_API_VERSION = "1"

_PY_VERSION = "{v.major}.{v.minor}.{v.micro}-{v.releaselevel}".format(
    v=_sys.version_info)

_UA = _f(
    "codePost API/v{_API_VERSION} "
    "SDK/v{_CODEPOST_SDK_VERSION} "
    "Python/v{_PY_VERSION}")

_APP_INFO_PATTERN = "{name}"

# Global submodule protected attributes
_logger = _logging.get_logger(name=_LOG_SCOPE)

# =============================================================================

class APIRequestor(object):

    def __init__(
        self,
        api_key=None,
        base_url=_config.BASE_URL,
        client=None,
        **kwargs
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._client = client

        if not self._api_key:
            # Try to retrieve a valid API key from the environment if the user
            # failed to provide a valid API key to the constructor
            self._api_key = _config.configure_api_key()
        
        _config.validate_api_key(self._api_key, log_outcome=True)
        
        if not isinstance(self._client, _httpclient.HTTPClient):
            # Reinitialize a default HTTPClient
            self._client = _httpclient.HTTPClient(**kwargs)
    
    @classmethod
    def _format_app_info(cls, **kwargs):
        s = ""
        d = kwargs if kwargs and len(kwargs) > 0 else codepost.app_info
        if isinstance(d, dict):
            if "name" in d:
                s += d.get("name")
                if "version" in d:
                    s += "/v{version} ".format(**d)
                if "url" in d:
                    s += " ({url})".format(**d)
        return s

    @classmethod
    def _build_headers(cls, api_key=None, method="get", **kwargs):
        
        # The SDK's user agent info
        user_agent = _UA

        # (Optionally) the client's user agent info
        app_str = ""
        if codepost.app_info:
            app_str = cls._format_app_info(**codepost.app_info)
            user_agent += " " + app_str

        # Diagnostic information
        diag = {
            "sdk": _CODEPOST_SDK_VERSION,
            "lang": "python",
            "publisher": "codepost",
            "lang_version": _PY_VERSION,
            "platform": _platform.platform(),
            "uname": _platform.uname(),
            "app": app_str,
        }

        headers = {
            "Authorization": "Token {}".format(api_key),
            "User-Agent": user_agent,
            "X-codePost-SDK-User-Agent": _json.dumps(diag)
        }

        if method == "post":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            headers.setdefault("Idempotency-Key", str(_uuid.uuid4()))
        
        return headers
    
    def _request(self, endpoint, method="get", **kwargs):
        kws = {}

        if kwargs and isinstance(kwargs, dict) and len(kwargs) > 0:
            kws.update(_copy.deepcopy(kwargs))
        
        kws["method"] = method
        
        # Configure API key

        api_key = kws.get("api_key", self._api_key)
        if "api_key" in kws:
            del kws["api_key"]

        # Compile headers

        default_headers = self._build_headers(
            api_key=api_key,
            **kws
        )
        kws["headers"] = kws.get("headers", dict())
        kws["headers"].update(default_headers)

        ret = self._client.request(
            url=urljoin(self._base_url, endpoint),
            **kws,
        )

        # Handle error codes here
        if not ret.status_code == 200:
            pass

        return ret

        



