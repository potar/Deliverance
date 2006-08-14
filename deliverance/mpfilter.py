"""
Deliverance theming for mod_python filters

Deliverance applies a theme to content.  This mod_python module acts as an 
Apache "filter", transforming content as it passes through Apache.

This module gets imported by mod_python during its startup.  Thus, the 
appmap instance becomes a global, computed only once.  If you need to 
recompute the theme, for example, restart the Apache.
"""
import time
from cStringIO import StringIO

from mod_python import apache
from deliverance.main import AppMap
appmap = AppMap() # Theme is generated once at module import time

def outputfilter(filter):
    if not hasattr(filter.req, 'notheme'):
        # Check for a flag to not apply theme
        args = filter.req.args
        if args and args.find("notheme") > -1:
            filter.req.notheme = True
        else:
            filter.req.notheme = False
            
    try:
        streambuffer = filter.req.streambuffer
    except AttributeError:
        if filter.req.notheme:
            # pass on if no theme
            filter.pass_on()
            return
        elif not filter.req.headers_out.has_key("content-type"):
            # pass on if no content type specified
            filter.pass_on()
            return
        elif not filter.req.headers_out["content-type"].startswith("text/html"):
            # pass on if not HTML
            filter.pass_on()
            return

        filter.req.streambuffer = StringIO()
        streambuffer = filter.req.streambuffer

    streamlet = filter.readline()
    while streamlet:
        streambuffer.write(streamlet)
        streamlet = filter.readline()

    if streamlet is None:
        output = appmap.publish(streambuffer.getvalue())
        filter.req.headers_out["Content-Length"] = str(len(output))
        filter.write(output)
        filter.close()


def handler(req):
    """Basic filter applying to all mime types it is registered for"""

    # Get the path, strip off leading slash, and convert to a 
    # dotted notation for xml:id compatibility
    path_info = req.path_info[1:]
    dotted_path = path_info.replace("/", ".")

    response = appmap.publish(dotted_path)
    req.content_type = "text/html"
    req.write(response)

    return apache.OK