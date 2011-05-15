import logging
import os, os.path, sys
import platform
import shutil
import cmd
import jsonpickle
import tempfile

from cStringIO import StringIO

from enthought.traits.api import HasTraits
from openmdao.main.variable import Variable

from multiprocessing.managers import BaseManager
from openmdao.main.factory import Factory
from openmdao.main.factorymanager import create
from openmdao.main.component import Component

from openmdao.lib.releaseinfo import __version__, __date__

from openmdao.main.project import *

from mdao_util import *

class ConsoleServerFactory(Factory):
    ''' creates and keeps track of :class:`ConsoleServer`s
    '''

    def __init__(self):
        super(ConsoleServerFactory, self).__init__()
        self.cserver_dict = {}
        self.temp_files = {}

    def __del__(self):
        ''' make sure we clean up on exit
        '''
        self.cleanup()

    def create(self, name, **ctor_args):
        """ Create a :class:`ConsoleServer` and return a proxy for it. """
        manager = BaseManager()
        manager.register('ConsoleServer', ConsoleServer)
        manager.start()
        return manager.ConsoleServer()
        
    def console_server(self,server_id):
        ''' create a new :class:`ConsoleServer` associated with an id
        '''
        if not self.cserver_dict.has_key(server_id):
            cserver = self.create('mdao-'+server_id)
            self.cserver_dict[server_id] = cserver;
        else:
            cserver = self.cserver_dict[server_id]
        return cserver
        
    def delete_server(self,server_id):
        ''' delete the :class:`ConsoleServer` associated with an id
        '''
        if self.cserver_dict.has_key(server_id):
            cserver = self.cserver_dict[server_id]
            del self.cserver_dict[server_id]
            cserver.cleanup()
            del cserver
        
    def get_tempdir(self,name):
        ''' create a temporary directory prefixed with the given name
        '''
        if not name in self.temp_files:
            self.temp_files[name] = tempfile.mkdtemp(prefix='mdao-'+name+'.')
        return self.temp_files[name]
        
    def cleanup(self):        
        ''' clean up temporary files, etc
        '''
        for server_id, cserver in self.cserver_dict:
            del self.cserver_dict[server_id]
            cserver.cleanup()
            del cserver            
        for name in self.temp_files:
            f = self.temp_files[name]
            if os.path.exists(f):
                rmtree(f)
                
class ConsoleServer(cmd.Cmd):
    """
    Object which knows how to load a model.
    Executes in a subdirectory of the startup directory.
    All remote file accesses must be within the tree rooted there.
    """

    def __init__(self, name='', host=''):
        cmd.Cmd.__init__(self)

        print '<<<'+str(os.getpid())+'>>> ConsoleServer ..............'
        
        #intercept stdout & stderr
        self.sysout = sys.stdout
        self.syserr = sys.stderr
        self.cout = StringIO()
        sys.stdout = self.cout
        sys.stderr = self.cout

        self.intro  = 'OpenMDAO '+__version__+' ('+__date__+')'
        self.prompt = 'OpenMDAO>> '
        
        self._hist    = []      ## No history yet
        self._locals  = {}      ## Initialize execution namespace for user
        self._globals = {}

        self.host = host
        self.pid = os.getpid()
        self.name = name or ('-cserver-%d' % self.pid)
        self.orig_dir = os.getcwd()
        self.root_dir = tempfile.mkdtemp(self.name)
        if os.path.exists(self.root_dir):
            logging.warning('%s: Removing existing directory %s',
                            self.name, self.root_dir)
            shutil.rmtree(self.root_dir)
        os.mkdir(self.root_dir)
        os.chdir(self.root_dir)
        
        print 'root_dir=',self.root_dir
        
        self.projfile = ''
        self.proj = None
        self.top = None
        
    def getcwd(self):
        return os.getcwd()

    def chdir(self, dirname):
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        os.chdir(dirname)
        sys.path[0] = dirname

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        self._hist += [ line.strip() ]
        return line

    def onecmd(self, line):
        self._hist += [ line.strip() ]
        # Override the onecmd() method so we can trap error returns
        try:
            cmd.Cmd.onecmd(self, line)
        except Exception, err:
            print 'The command returned an error: %s\n' % str(err)

    def emptyline(self):
        # Default for empty line is to repeat last command - yuck
        pass

    def default(self, line):       
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """
        isStatement = False
        try:
            code = compile(line, '<string>', 'eval')
        except SyntaxError:
            isStatement = True
            
        if isStatement:
            try:
                exec(line) in self._locals, self._globals
            except Exception, e:
                print str(e.__class__.__name__), ":", e
        else:
            try:
                result = eval(line, self._globals, self._locals)
                if result is not None:
                    print result
            except Exception, e:
                print str(e.__class__.__name__), ":", e

    def run(self):
        """ run the model (i.e. the top assembly) """
        if self.top:
            self.top.run()
        else:
            print "Execution failed: No top level assembly was found."
        
    def execfile(self, file):
        """ execfile in server's globals. """        
        # set name so any "if __name__ == __main__" code will be executed
        self._globals['__name__'] = '__main__'
        execfile(file,self._globals)

    def get_output(self):
        """ get any pending output and clear the outputput buffer """
        output = self.cout.getvalue()     
        self.cout.truncate(0)
        return output
        
    def get_pid(self):
        """ Return this server's :attr:`pid`. """
        return self.pid
        
    def get_project(self):
        """ Return the current model as a project archive. """
        return self.proj

    def get_history(self):
        """ Return this server's :attr:`_hist`. """
        return self._hist

    def get_JSON(self):
        """ return current state as JSON """
        return jsonpickle.encode(self._globals)
        
    def _get_components(self,cont):
        comps = {}
        for n,v in cont.items():
            if isinstance(v, HasTraits):
                if isinstance(v,Component):
                    comps[n] = self._get_components(v)
                else:
                    comps[n] = v
        return comps
        
    def get_components(self):
        """ get hierarchical dictionary of openmdao objects """
        comps = {}
        if self.top:
            comps = self._get_components(self.top)
        return comps

    def _get_attributes(self,obj):
        """ get attributes of object """
        attr = {}
        for n,v in obj.items():
            if isinstance(v,Component):
                attr[n] = self._get_attributes(v)
            else:
                attr[n] = v
        return attr
        
    def get_attributes(self,name):
        attr = {}
        if self.top:
            attr = self._get_attributes(self.top.get(name))
        return attr
    
    def get_workingtypes(self):
        """ Return this server's user defined types. """
        types = []
        g = self._globals.items()
        for k,v in g:
            if (type(v).__name__ == 'classobj') or str(v).startswith('<class'):
                obj = self._globals[k]()
                if isinstance(obj, HasTraits):
                    types.append( ( k , 'n/a') )
        return types

    def load_project(self,filename):
        print 'loading project from:',filename
        self.projfile = filename
        self.proj = project_from_archive(filename,dest_dir=self.getcwd())
        self.top = self.proj.top
        set_as_top(self.top)
        
    def save_project(self):
        """ save the cuurent project state & export it whence it came
        """
        if self.proj:
            try:
                self.proj.save()
                print 'Project state saved.'
                if len(self.projfile)>0:
                    dir = os.path.dirname(self.projfile)
                    ensure_dir(dir)
                    self.proj.export(destdir=dir)
                    print 'Exported to ',dir+'/'+self.proj.name
                else:
                    print 'Export failed, directory not known'
            except Exception, err:
                print "Save failed:", str(err)                
        else:
            print 'No Project to save'

    def add_component(self,name,classname):
        """ add a new component of the given type to the top assembly. """
        try:
            if (classname.find('.')>0):
                self.top.add(name,create(classname))
            else:
                self.top.add(name,self._globals[classname]())
        except Exception, err:
            print "Add component failed:", str(err)
            
    def create(self,typname,name):
        """ create a new object of the given type. """
        try:
            if (typname.find('.') < 0):
                self.default(name+'='+typname+'()')
            else:
                self._globals[name]=create(typname)
        except Exception, err:
            print "create failed:", str(err)
            
        return self._globals

    def cleanup(self):
        """ Cleanup this server's directory. """
        self.stdout = self.sysout
        self.stderr = self.syserr
        logging.shutdown()
        os.chdir(self.orig_dir)
        if os.path.exists(self.root_dir):
            try:
                print "trying to rmtree ",self.root_dir
                shutil.rmtree(self.root_dir)
            except e:
                print "failed to rmtree ",self.root_dir
                print e
        
    def get_files(self):
        ''' get a nested dictionary of files in the working directory
        '''
        cwd = os.getcwd()
        return filedict(cwd,root=cwd)

    def get_file(self,filename):
        ''' get contents of file in working directory
            returns None if file was not found
        '''
        filepath = os.getcwd()+'/'+str(filename)
        if os.path.exists(filepath):
            contents=open(filepath, 'r').read()
            return contents
        else:
            return None
            
    def write_file(self,filename,contents):
        ''' write contents to file in working directory
        '''
        filepath = os.getcwd()+'/'+str(filename)
        fout = open(filepath,'wb')
        fout.write(contents)
        fout.close()
    
    def delete_file(self,filename):
        ''' delete file in working directory
            returns False if file was not found, otherwise returns True
        '''
        filepath = os.getcwd()+'/'+str(filename)
        if os.path.exists(filepath):
            if os.path.isdir(filepath):
                os.rmdir(filepath)
            else:
                os.remove(filepath)
            return True
        else:
            return False
            
    def ensure_dir(self,dirname):
        ''' create directory in working directory
            (does nothing if directory already exists)
        '''
        dirpath = os.getcwd()+'/'+str(dirname)
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
            