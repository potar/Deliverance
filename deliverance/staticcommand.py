"""
Command for rendering a set of static files to another set of static
files.  Not yet complete. 
"""

import optparse
import sys
import os
import re
import urllib
import cgi
import pkg_resources

my_package = pkg_resources.get_distribution('Deliverance')

scheme_re = re.compile(r'^[a-z][a-z]+:', re.I)
drive_re = re.compile(r'^[a-z]:', re.I)

help = """\
Render the FILES (or directories) given the THEME and RULES
(or a default set of rules generated by the rule-* options)"""

parser = optparse.OptionParser(
    version=str(my_package),
    usage="%%prog [OPTIONS] INPUT_DIR OUTPUT_DIR\n\n%s" % help)
parser.add_option('-v', '--verbose',
                  help="Be more verbose",
                  dest="verbose",
                  action="count")
parser.add_option('-q', '--quiet',
                  help="Be more quiet",
                  dest="quiet",
                  action="count")
parser.add_option('-t', '--theme',
                  help="The URI of the theme to use",
                  metavar="URI/FILE",
                  dest="theme")
parser.add_option('-r', '--rule',
                  help="The URI of the ruleset to use",
                  metavar="URI/FILE",
                  dest="rule")
parser.add_option('--rule-theme-body',
                  metavar="XPATH",
                  help="If no rules provided, use this XPath expression to locate the body",
                  dest="theme_body_xpath")
parser.add_option('--rule-content-body',
                  metavar="XPATH",
                  help="If no rules provided, use this XPath expression to locate the content body")
parser.add_option('--renderer',
                  dest="renderer",
                  metavar="NAME",
                  help="Select which renderer to use: 'py' or 'xslt'",
                  default='py')

class BadCommand(Exception):
    pass

def run_command(options, args):
    if len(args) < 2:
        raise BadCommand(
            "You must give a INPUT_DIR and OUTPUT_DIR argument")
    elif len(args) > 2:
        raise BadCommand(
            "You can only give two arguments, INPUT_DIR and OUTPUT_DIR")
    input_dir, output_dir = args
    if not options.rule:
        options.rule = make_rule(options)
    else:
        options.rule = make_uri(options.rule)
    options.verbose += 1
    options.verbose -= options.quiet
    del options.quiet
    if not options.theme:
        raise BadCommand(
            "You must give an argument for --theme")
    options.theme = make_uri(options.theme)
    loader = make_loader(input_dir, options.rule)
    norm_input_dir = os.path.abspath(input_dir)
    renderer = None
    for fn in all_files(input_dir):
        full_fn = os.path.abspath(fn)
        assert full_fn.startswith(input_dir)
        plain_fn = full_fn[len(input_dir):].lstrip(os.path.sep)
        dest_fn = os.path.join(output_dir, plain_fn)
        ext = os.path.splitext(fn)[1].lower()
        if ext not in ('.html', '.xhtml'):
            if options.verbose > 2:
                print 'Copying %s' % fn
            shutil.copy(fn, dest_fn)
            continue
        if options.verbose > 2:
            print 'Rendering %s'
        contents = transform_file(renderer, loader, fn)
        f = open(dest_fn, 'wb')
        f.write(contents)
        f.close()


def all_files(dir):
    for dirpath, dirnames, filenames in os.walk(dir):
        for filename in filenames:
            yield os.path.join(dirpath, filename)

def make_uri(maybe_uri):
    """
    Returns the argument as a URI.  The argument may be a relative or
    absolute file path, in which case it is turned into an absolute
    file: URI.
    """
    if scheme_re.search(maybe_uri):
        return maybe_uri
    maybe_uri = os.path.abspath(maybe_uri)
    if os.path.sep != '/':
        maybe_uri = maybe_uri.replace(os.path.sep, '/')
    maybe_uri = urllib.quote(maybe_uri)
    if sys.platform == 'win32':
        match = drive_re.search(maybe_uri)
        if match:
            maybe_uri = '/' + maybe_uri[:match.end()-1] + '|' + maybe_uri[match.end():]
    return 'file://' + maybe_uri

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    options, args = parser.parse_args(args)
    try:
        run_command(options, args)
    except BadCommand, e:
        print e
        parser.print_help()
        sys.exit(2)
        

if __name__ == '__main__':
    main()
    
