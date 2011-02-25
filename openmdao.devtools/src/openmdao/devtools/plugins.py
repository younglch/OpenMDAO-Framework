
import os
import sys
import pprint
import StringIO

from openmdao.util.fileutil import build_directory

templates = {}

templates['conf.py'] = """

# -*- coding: utf-8 -*-
#
# This file is execfile()d with the current directory set to its containing dir.
#
# The contents of this file are pickled, so don't put values in the namespace
# that aren't pickleable (module imports are okay, they're removed automatically).
#

import sys, os

# General configuration
# ---------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 
              'sphinx.ext.doctest', 'sphinx.ext.todo', 
              'openmdao.util.doctools', 'sphinx.ext.viewcode'
      ]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'%(name)s'
copyright = u'%(copyright)s'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '%(version)s'
#The short version is the one that shows up in the file when you use /version/.
# The full version, including alpha/beta/rc tags.
release = '%(release)s'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = '%%B %%d, %%Y'

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ['_build']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# Options for HTML output
# -----------------------

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
html_style = 'default.css'

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%%b %%d, %%Y'

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, the reST sources are included in the HTML build as _sources/<name>.
#html_copy_source = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

html_theme = "default"
html_theme_options = {
     "headtextcolor": "darkred",
     "headbgcolor": "gainsboro",
     "headfont": "Arial",
     "relbarbgcolor": "black",
     "relbartextcolor": "white",
     "relbarlinkcolor": "white",
     "sidebarbgcolor": "gainsboro",
     "sidebartextcolor": "darkred",
     "sidebarlinkcolor": "black",
     "footerbgcolor": "gainsboro",
     "footertextcolor": "darkred",
     "textcolor": "black",
     "codebgcolor": "#FFFFCC",
     "linkcolor": "darkred",
     "codebgcolor": "#ffffcc",
    }

todo_include_todos = True

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'http://docs.python.org/dev': None}

autodoc_member_order = 'groupwise'

"""

templates['index.rst'] = """

%(title_marker)s
%(name)s Documentation
%(title_marker)s

Current version: |version|

Contents:

.. toctree::
   :maxdepth: 2
    
   %(doc)s
   srcdocs

  
"""

templates['srcdocs.rst'] = """

====================
Source Documentation
====================

.. automodule:: %(name)s
   :members:
   :undoc-members:
   :show-inheritance:

"""

templates['setup.py'] = """

#
# This file is autogenerated during plugin_quickstart
#

import sys
import os

name = '%(name)s'

# add our package to python path so autodoc will find our source code
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),'src',name))

kwargs = %(setup_options)s

from setuptools import setup

building = set([
 'build',
 'bdist',
 'sdist',
 'bdist_egg',
 'bdist_rpm',
 'bdist_wininst',
 'build_ext',
 'build_py',
])

# ensure that docs are built during any build command (assuming sphinx is available)
for arg in sys.argv[1:]:
    if arg in building:
        if 'build_sphinx' not in sys.argv:
            try:
                from sphinx.setup_command import BuildDoc
            except ImportError:
                pass
            else:
                sys.argv = [sys.argv[0], 'build_sphinx']+sys.argv[1:]
        break

# only import BuildDoc if we're building so we can avoid a sphinx
# dependency when we don't really need it
if 'build_sphinx' in sys.argv:
    from sphinx.setup_command import BuildDoc
    kwargs['cmdclass'] = { 
         'build_sphinx': BuildDoc,
    }
    mydir = os.path.dirname(os.path.abspath(__file__))
    docbuilddir = os.path.join(mydir, 'src', '%(name)s', 'sphinx_build')
    if not os.path.isdir(docbuilddir):
        os.mkdir(docbuilddir)

setup(**kwargs)

"""

templates['setup.cfg'] = """

[build_sphinx]
version = %(version)s
release = %(release)s
all-files = true
build_dir = src/%(name)s/sphinx_build

"""

templates['MANIFEST.in'] = """

graft src/%(name)s/sphinx_build/html

"""

code_templates = {}

code_templates['openmdao.component'] = """

from openmdao.main.api import Component, plugin
from openmdao.lib.datatypes.api import Float

@plugin('openmdao.component')
class %(name)s(Component):
    # declare inputs and outputs here
    #x = Float(0.0, iotype='in')
    #y = Float(0.0, iotype='out')

    def execute(self):
        # do your calculations here
        pass
        
"""

code_templates['openmdao.driver'] = """

from openmdao.main.api import Driver
from openmdao.util.decorators import add_delegate

class %(name)s(Driver):

    def start_iteration(self):
        super(%(name)s, self).start_iteration()

    def continue_iteration(self):
        return super(%(name)s, self).continue_iteration()
    
    def pre_iteration(self):
        super(%(name)s, self).pre_iteration()
        
    def run_iteration(self):
        super(%(name)s, self).run_iteration()

    def post_iteration(self):
        super(%(name)s, self).post_iteration()

"""

def argv_to_args(argv=None):
    """Convert command line arguments into arguments passable to a python
    callable.
    
    argv: str (optional)
        A list of argument strings.  If None (the default), then sys.argv[1:]
        will be used.
    
    Returns a tuple of the form (args, kwargs).
    """
    if argv is None:
        argv = sys.argv[1:]
        
    args = []
    kwargs = {}
    
    if len(argv) == 0:
        return (args, kwargs)

    for i,arg in enumerate(argv):
        if '=' in arg:
            break
        args.append(arg)
    else:
        return (args, kwargs)
        
    for arg in argv[i:]:
        if '=' in arg:
            lhs,rhs = arg.split('=',1)
            kwargs[lhs.strip()] = rhs.strip()
        else:
            raise RuntimeError("argv_to_args: positional arg (%s) appeared after named args" %
                               arg)
    
    return (args, kwargs)


def plugin_quickstart(argv=None):
    """A command line script (plugin_quickstart) points to this.  It generates a
    directory structure for an openmdao plugin package along with Sphinx docs.
    
    usage: plugin_quickstart <plugin_name> <version> [destination_dir] [<name>=<option>]*
    
    For each <name>=<option> argument, <name> can be any valid keyword passable to the 
    setup function, or one of the keywords listed below:
    
    src:  the path to a python source file containing the plugin class definition(s)
    doc: the path to a .rst file containing docs for the plugin
    group: a plugin group id, e.g., openmdao.component, openmdao.driver, etc.

    """
    
    args, kwargs = argv_to_args(argv)

    if not args:
        raise RuntimeError("plugin_quickstart: no plugin name was specified")
    elif len(args) < 2:
        raise RuntimeError("plugin_quickstart: no version specified")
    elif len(args) > 2:
        raise RuntimeError("plugin_quickstart: don't understand args %s" % args[2:])

    plugin_name = args[0]
    version = args[1]
    dest = '.' if len(args) < 3 else args[2]
    
    pyfile = kwargs.pop('src', None)
    group = kwargs.pop('group', 'openmdao.component')
    plugin_template = kwargs.pop('doc', '')
    cpyright = kwargs.pop('copyright', '')
    release = kwargs.pop('release', version)

    setup_options = {
        'name': plugin_name,
        'version': version,
        'packages': [plugin_name],
        'package_data': { plugin_name: [
            'sphinx_build/html/*.*',
            'sphinx_build/html/_modules/*',
            'sphinx_build/html/_sources/*',
            'sphinx_build/html/_static/*',
            ] },
        'package_dir': {'': 'src'},
        'zip_safe': False,
        'include_package_data': True,
        'install_requires': [],
        'url': 'UNKNOWN',
        'author': 'UNKNOWN',
        'author_email': 'UNKNOWN',
    }
    
    setup_options.update(kwargs)
    
    sio = StringIO.StringIO()
    pprint.pprint(setup_options, sio)
    
    template_options = {
        'doc': plugin_template,
        'copyright': cpyright,
        'release': release,
        'title_marker': '='*(len(plugin_name)+len(' Documentation')),
        'setup_options': sio.getvalue()
    }
    
    template_options.update(setup_options)
    
    if pyfile:
        f = open(pyfile, 'r')
        plugin_py_template = f.read()
        f.close()
    else:
        plugin_py_template = code_templates[group or 'openmdao.component']

    dirstruct = {
        plugin_name: {
            'src': {
                plugin_name: {
                    '__init__.py': '',
                    '%s.py' % plugin_name: plugin_py_template % template_options,
                    },
                },
            'docs': {
                'conf.py': templates['conf.py'] % template_options,
                'index.rst': templates['index.rst'] % template_options,
                'srcdocs.rst': templates['srcdocs.rst'] % template_options,
                '%s.rst' % plugin_name: plugin_template % template_options,
                },
            'setup.cfg': templates['setup.cfg'] % template_options,
            'setup.py': templates['setup.py'] % template_options,
            'MANIFEST.in': templates['MANIFEST.in'] % template_options,
            'README.txt': 'README.txt file for %s' % plugin_name,
        }
    }
    
    startdir = os.getcwd()
    try:
        os.chdir(dest)
        build_directory(dirstruct)
    
    finally:
        os.chdir(startdir)
        

