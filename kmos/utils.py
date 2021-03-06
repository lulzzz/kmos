#!/usr/bin/env python
"""Several utility functions that do not seem to fit somewhere
   else.
"""
#    Copyright 2009-2012 Max J. Hoffmann (mjhoffmann@gmail.com)
#    This file is part of kmos.
#
#    kmos is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    kmos is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with kmos.  If not, see <http://www.gnu.org/licenses/>.

from StringIO import StringIO

try:
    from kiwi.datatypes import ValidationError
except:
    ValidationError = UserWarning


class CorrectlyNamed:
    """Syntactic Sugar class for use with kiwi, that makes sure that the name
    field of the class has a name field, that always complys with the rules
    for variables.
    """

    def __init__(self):
        pass

    def on_name__validate(self, _, name):
        """Called by kiwi upon chaning a string
        """
        if ' ' in name:
            return ValidationError('No spaces allowed')
        elif name and not name[0].isalpha():
            return ValidationError('Need to start with a letter')


def write_py(fileobj, images, **kwargs):
    """Write a ASE atoms construction string for `images`
       into `fileobj`.
    """
    if isinstance(fileobj, str):
        fileobj = open(fileobj, 'w')

    scaled_positions = kwargs['scaled_positions'] \
        if 'scaled_positions' in kwargs else True
    fileobj.write('from ase import Atoms\n\n')
    fileobj.write('import numpy as np\n\n')

    if not isinstance(images, (list, tuple)):
        images = [images]
    fileobj.write('images = [\n')

    for image in images:
        fileobj.write("    Atoms(symbols='%s',\n"
                      "          pbc=np.%s,\n"
                      "          cell=np.array(\n      %s,\n" % (
            image.get_chemical_symbols(reduce=True),
            repr(image.pbc),
            repr(image.cell)[6:]))

        if not scaled_positions:
            fileobj.write("          positions=np.array(\n      %s),\n"
                % repr(list(image.positions)))
        else:
            fileobj.write("          scaled_positions=np.array(\n      %s),\n"
                % repr(list(image.get_scaled_positions().tolist())))
        fileobj.write('),\n')

    fileobj.write(']')


def get_ase_constructor(atoms):
    """Return the ASE constructor string for `atoms`."""
    if type(atoms) is type(str):
        atoms = eval(atoms)
    if type(atoms) is list:
        atoms = atoms[0]
    f = StringIO()
    write_py(f, atoms)
    f.seek(0)
    lines = f.readlines()
    f.close()
    astr = ''
    for i, line in enumerate(lines):
        if i >= 5 and i < len(lines) - 1:
            astr += line
    #astr = astr[:-2]
    return astr.strip()


def product(*args, **kwds):
    """Take two lists and return iterator producing
    all combinations of tuples between elements
    of the two lists."""
    # product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
    # product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
    pools = [tuple(arg) for arg in args] * kwds.get('repeat', 1)
    result = [[]]
    for pool in pools:
        result = [x + [y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)


def split_sequence(seq, size):
    """Take a list and a number n and return list
       divided into n sublists of roughly equal size.
    """
    newseq = []
    splitsize = 1.0 / size * len(seq)
    for i in range(size):
        newseq.append(seq[int(round(i * splitsize)):
                      int(round((i + 1) * splitsize))])
    return newseq


def download(project):
    from django.http import HttpResponse
    import zipfile
    import tempfile
    from os.path import join, basename
    from glob import glob
    from kmos.io import import_xml, export_source

    # return HTTP download response (e.g. via django)
    response = HttpResponse(mimetype='application/x-zip-compressed')
    response['Content-Disposition'] = 'attachment; filename="kmos_export.zip"'

    if isinstance(project, basestring):
        project = import_xml(project)

    try:
        from cStringIO import StringIO
    except:
        from StringIO import StringIO
    stringio = StringIO()
    zfile = zipfile.ZipFile(stringio, 'w')

    # save XML
    zfile.writestr('project.xml', str(project))

    # generate source
    tempdir = tempfile.mkdtemp()
    srcdir = join(tempdir, 'src')

    # add kMC project sources
    export_source(project, srcdir)
    for srcfile in glob(join(srcdir, '*')):
        zfile.write(srcfile, join('src', basename(srcfile)))

    # add standalone kmos program
    # TODO

    # write temporary file to response
    zfile.close()
    stringio.flush()
    response.write(stringio.getvalue())
    stringio.close()
    return response


def evaluate_kind_values(infile, outfile):
    """Go through a given file and dynamically
    replace all selected_int/real_kind calls
    with the dynamically evaluated fortran code
    using only code that the function itself
    contains.

    """
    import re
    import os
    import imp
    import sys
    sys.path.append(os.path.abspath(os.curdir))
    def import_selected_kind():
        """Tries to import the module which provides
        processor dependent kind values. If the module
        is not available it is compiled from a here-document
        and imported afterwards.

        Warning: creates both the source file and the
        compiled module in the current directory.

        """
        try:
            import f2py_selected_kind
        except:
            from numpy.f2py import compile
            fcode = """module kind
    implicit none
    contains
    subroutine real_kind(p, r, kind_value)
      integer, intent(in), optional :: p, r
      integer, intent(out) :: kind_value

      if(present(p).and.present(r)) then
        kind_value = selected_real_kind(p=p, r=r)
      else
        if (present(r)) then
          kind_value = selected_real_kind(r=r)
        else
          if (present(p)) then
            kind_value = selected_real_kind(p)
          endif
        endif
      endif
    end subroutine real_kind

    subroutine int_kind(p, r, kind_value)
      integer, intent(in), optional :: p, r
      integer, intent(out) :: kind_value

      if(present(p).and.present(r)) then
        kind_value = selected_int_kind(p)
      else
        if (present(r)) then
          kind_value = selected_int_kind(r=r)
        else
          if (present(p)) then
            kind_value = selected_int_kind(p)
          endif
        endif
      endif
    end subroutine int_kind

    end module kind
            """
            # quick'n'dirty workaround for windoze
            if os.name == 'nt':
                with open('f2py_selected_kind.f90', 'w') as f:
                    f.write(fcode)
                from copy import deepcopy
                # save for later
                true_argv = deepcopy(sys.argv)
                sys.argv = ('%s -c --fcompiler=gnu95 --compiler=mingw32 -m f2py_selected_kind f2py_selected_kind.f90' % sys.executable).split()
                from numpy import f2py as f2py2e
                f2py2e.main()

                sys.argv = true_argv
            else:
                compile(fcode, source_fn='f2py_selected_kind.f90',
                        modulename='f2py_selected_kind')
            try:
                import f2py_selected_kind
            except:
                print(os.path.abspath(os.curdir))
                print(os.listdir('.'))
                raise
        return f2py_selected_kind.kind


    def parse_args(args):
        """
            Parse the arguments for selected_(real/int)_kind
            to pass them on to the Fortran module.

        """
        in_args = [x.strip() for x in args.split(',')]
        args = []
        kwargs = {}

        for arg in in_args:
            if '=' in arg:
                symbol, value = arg.split('=')
                kwargs[symbol] = eval(value)
            else:
                args.append(eval(arg))

        return args, kwargs


    def int_kind(args):
        """Python wrapper around Fortran selected_int_kind
        function.
        """
        args, kwargs = parse_args(args)
        return import_selected_kind().int_kind(*args, **kwargs)


    def real_kind(args):
        """Python wrapper around Fortran selected_real_kind
        function.
        """
        args, kwargs = parse_args(args)
        return import_selected_kind().real_kind(*args, **kwargs)




    infile = file(infile)
    outfile = file(outfile, 'w')
    int_pattern = re.compile((r'(?P<before>.*)selected_int_kind'
                              '\((?P<args>.*)\)(?P<after>.*)'),
                              flags=re.IGNORECASE)
    real_pattern = re.compile((r'(?P<before>.*)selected_real_kind'
                                '\((?P<args>.*)\)(?P<after>.*)'),
                              flags=re.IGNORECASE)

    for line in infile:
        real_match = real_pattern.match(line)
        int_match = int_pattern.match(line)
        if int_match:
            match = int_match.groupdict()
            line = '{before}{kind}{after}\n'.format(
                    before=match['before'],
                    kind=int_kind(match['args']),
                    after=match['after'],)
        elif real_match:
            match = real_match.groupdict()
            line = '{before}{kind}{after}\n'.format(
                    before=match['before'],
                    kind=real_kind(match['args']),
                    after=match['after'],)
        outfile.write(line)
    infile.close()
    outfile.close()


def build(options):
    from os.path import isfile
    from os import system, name
    import sys

    src_files = 'kind_values_f2py.f90 base.f90 lattice.f90 proclist.f90'

    if name == 'nt':
        interpreter = 'python '
        options.fcompiler = 'gnu95'
    elif name == 'posix':
        interpreter = ''
    else:
        interpreter = ''

    extra_flags = {}
    extra_flags['gfortran'] = ('-ffree-line-length-none -ffree-form'
                               ' -xf95-cpp-input -Wall -g')
    extra_flags['gnu95'] = extra_flags['gfortran']
    extra_flags['intel'] = '-fast -fpp -Wall -I/opt/intel/fc/10.1.018/lib'
    extra_flags['intelem'] = '-fast -fpp -Wall -g'

    # FIXME
    extra_libs = ''
    ccompiler = ''
    if name == 'nt':
        ccompiler = '--compiler=mingw32'
        if sys.version_info < (2, 7):
            extra_libs = ' -lmsvcr71 '
        else:
            extra_libs = ' -lmsvcr90 '

    module_name = 'kmc_model'


    if not isfile('kind_values_f2py.py'):
         evaluate_kind_values('kind_values.f90', 'kind_values_f2py.f90')

    for src_file in src_files.split():
        if not isfile(src_file):
            raise IOError('File %s not found' % src_file)

    call = []
    call.append('-c')
    call.append('-c')
    call.append('--fcompiler=%s' % options.fcompiler)
    if name == 'nt':
        call.append('%s' % ccompiler)
    #call += extra_libs.split()
    call.append('--f90flags="%s"' % extra_flags.get(
                                        options.fcompiler, ''))
    call.append('-m')
    call.append(module_name)
    call += src_files.split()

    print(call)
    #exit()
    from copy import deepcopy
    true_argv = deepcopy(sys.argv)  # save for later
    from numpy import f2py
    sys.argv = call
    f2py.main()
    sys.argv = true_argv
