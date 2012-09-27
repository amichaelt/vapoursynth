#!/usr/bin/env python

import os, subprocess
from waflib import Task, TaskGen, Utils

APPNAME = 'VapourSynth'
VERSION = '8'

TOP = os.curdir
OUT = 'build'

class preproc(Task.Task):
    "Preprocess Cython source files"

    ext_out = ['.pyx']
    inst_to = None
    color = 'CYAN'

    def run(self):
        if self.env.CXX_NAME == 'gcc':
            params = ['-E', '-x', 'c']
        elif self.env.CXX_NAME == 'msvc':
            params = ['/E']

        args = [Utils.subst_vars('${CC}', self.env)] + params + [self.inputs[0].abspath()]

        with open(self.outputs[0].abspath(), 'w') as f:
            subprocess.Popen(args, stdout = f).wait()

@TaskGen.extension('.pyx')
def add_pyx_file(self, node):
    self.create_task('preproc', node, node.get_bld().change_ext('.pyx'))

def options(opt):
    opt.load('compiler_c')
    opt.load('compiler_cxx')
    opt.load('qt4')

    opt.add_option('--mode', action = 'store', default = 'debug', help = 'the mode to compile in (debug/release)')
    opt.add_option('--static', action = 'store', default = 'false', help = 'build a static library (true/false)')
    opt.add_option('--filters', action = 'store', default = 'true', help = 'build included filters (true/false)')
    opt.add_option('--cython', action = 'store', default = 'true', help = 'build Cython wrapper (true/false)')

def configure(conf):
    def add_options(flags, options):
        for flag in flags:
            for option in options:
                if option not in conf.env[flag]:
                    conf.env.append_value(flag, option)

    conf.load('compiler_c')
    conf.load('compiler_cxx')
    conf.load('qt4')

    # Load Yasm explicitly, then the Nasm module which
    # supports both Nasm and Yasm.
    conf.find_program('yasm', var = 'AS', mandatory = True)
    conf.load('nasm')

    if conf.env.DEST_OS == 'darwin':
        if conf.env.CXX_NAME == 'gcc':
            add_options(['ASFLAGS'],
                        ['-DPREFIX'])

    if conf.env.CXX_NAME == 'gcc':
        add_options(['CFLAGS', 'CXXFLAGS'],
                    ['-DVSCORE_EXPORTS',
                     '-fPIC'])
    elif conf.env.CXX_NAME == 'msvc':
        add_options(['CFLAGS', 'CXXFLAGS'],
                    ['/DVSCORE_EXPORTS',
                     '/EHsc',
                     '/Zc:wchar_t-'])

    add_options(['ASFLAGS'],
                ['-w',
                 '-Worphan-labels',
                 '-Wunrecognized-char'])

    if conf.env.DEST_CPU in ['x86_64', 'amd64', 'x64']:
        add_options(['ASFLAGS'],
                    ['-DARCH_X86_64=1'])

        if conf.env.DEST_OS == 'darwin':
            fmt = 'macho64'
        elif conf.env.DEST_OS == 'win32':
            fmt = 'win64'
        else:
            fmt = 'elf64'
    else:
        add_options(['ASFLAGS'],
                    ['-DARCH_X86_64=0'])

        if conf.env.DEST_OS == 'darwin':
            fmt = 'macho32'
        elif conf.env.DEST_OS == 'win32':
            fmt = 'win32'
        else:
            fmt = 'elf32'

    add_options(['ASFLAGS'],
                ['-f{0}'.format(fmt)])

    if conf.options.mode == 'debug':
        if conf.env.CXX_NAME == 'gcc':
            add_options(['CFLAGS', 'CXXFLAGS'],
                        ['-DVSCORE_DEBUG',
                         '-g',
                         '-ggdb',
                         '-ftrapv'])
        elif conf.env.CXX_NAME == 'msvc':
            add_options(['CFLAGS', 'CXXFLAGS'],
                        ['/DVSCORE_DEBUG',
                         '/Z7'])

        add_options(['ASFLAGS'],
                    ['-DVSCORE_DEBUG'])
    elif conf.options.mode == 'release':
        if conf.env.CXX_NAME == 'gcc':
            add_options(['CFLAGS', 'CXXFLAGS'],
                        ['-O3'])
        elif conf.env.CXX_NAME == 'msvc':
            add_options(['CFLAGS', 'CXXFLAGS'],
                        ['/Ox'])
    else:
        conf.fatal('--mode must be either debug or release.')

    # Waf always uses gcc/g++ for linking when using a GCC
    # compatible C/C++ compiler.
    if conf.env.CXX_NAME == 'gcc':
        add_options(['LINKFLAGS_cxxshlib', 'LINKFLAGS_cxxprogram'],
                    ['-Wl,-Bsymbolic'])

    conf.env.STATIC = conf.options.static

    if not conf.env.STATIC in ['true', 'false']:
        conf.fatal('--static must be either true or false.')

    conf.env.FILTERS = conf.options.filters

    if not conf.env.FILTERS in ['true', 'false']:
        conf.fatal('--filters must be either true or false.')

    conf.env.CYTHON = conf.options.cython

    if not conf.env.CYTHON in ['true', 'false']:
        conf.fatal('--cython must be either true or false.')

    conf.check_cxx(lib = 'QtCore', features = 'cxx cxxprogram')

    conf.check_cc(lib = 'avutil')
    conf.check_cc(header_name = 'libavutil/avutil.h')
    conf.check_cc(lib = 'avutil', header_name = 'libavutil/avutil.h', function_name = 'avutil_license')

    conf.check_cc(lib = 'swscale')
    conf.check_cc(header_name = 'libswscale/swscale.h')
    conf.check_cc(lib = 'swscale', header_name = 'libswscale/swscale.h', function_name = 'swscale_license')

def build(bld):
    def search_paths(paths):
        srcpaths = []

        for path in paths:
            srcpaths += [os.path.join(path, '*.c'),
                         os.path.join(path, '*.cpp'),
                         os.path.join(path, '*.asm')]

        return srcpaths

    sources = search_paths([os.path.join('src', 'core'),
                            os.path.join('src', 'core', 'asm')])

    if bld.env.DEST_OS == 'win32':
        sources += search_paths([os.path.join('src', 'avisynth')])

    bld(features = 'c qxx asm',
        includes = 'include',
        use = ['QTCORE', 'AVUTIL', 'SWSCALE'],
        source = bld.path.ant_glob(sources),
        target = 'objs')

    bld(features = 'c qxx asm cxxshlib',
        use = ['objs'],
        target = 'vapoursynth')

    if bld.env.STATIC == 'true':
        bld(features = 'c qxx asm cxxstlib',
            use = ['objs', 'QTCORE', 'AVUTIL', 'SWSCALE'],
            target = 'vapoursynth')

    if bld.env.FILTERS == 'true':
        bld(features = 'c qxx asm cxxshlib',
            includes = 'include',
            use = ['vapoursynth'],
            source = bld.path.ant_glob(search_paths([os.path.join('src', 'filters', 'eedi3')])),
            target = 'eedi3',
            install_path = '${PREFIX}/lib/vapoursynth')

    if bld.env.CYTHON == 'true':
        bld(features = 'preproc',
            source = bld.path.ant_glob([os.path.join('src', 'cython', '*.pyx')]),
            use = ['objs'])

    bld.install_files('${PREFIX}/include', os.path.join('include', 'VapourSynth.h'))
