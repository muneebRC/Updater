import os
import shutil
import sys
from configparser import ConfigParser
from tkinter import messagebox
import subprocess

src = r'PATH_TO latest version'
update_ini = r'PATH_TO version file'

def get_app_name(src):
    app_name = []
    for i in reversed(src):
        if i == '\\':
            break
        else:
            app_name.append(i)
    return ''.join(reversed(app_name))

app_name = get_app_name(src)
dst = os.getcwd()

"""Progress bar code orginally written by flutefreak7 (Stackoverflow)"""
def progress_percentage(perc, width=None):
    # This will only work for python 3.3+ due to use of
    # os.get_terminal_size the print function etc.

    FULL_BLOCK = '█'
    # this is a gradient of incompleteness
    INCOMPLETE_BLOCK_GRAD = ['░', '▒', '▓']

    assert(isinstance(perc, float))
    assert(0. <= perc <= 100.)
    # if width unset use full terminal
    if width is None:
        width = os.get_terminal_size().columns
    # progress bar is block_widget separator perc_widget : ####### 30%
    max_perc_widget = '[100.00%]' # 100% is max
    separator = ' '
    blocks_widget_width = width - len(separator) - len(max_perc_widget)
    assert(blocks_widget_width >= 10) # not very meaningful if not
    perc_per_block = 100.0/blocks_widget_width
    # epsilon is the sensitivity of rendering a gradient block
    epsilon = 1e-6
    # number of blocks that should be represented as complete
    full_blocks = int((perc + epsilon)/perc_per_block)
    # the rest are "incomplete"
    empty_blocks = blocks_widget_width - full_blocks

    # build blocks widget
    blocks_widget = ([FULL_BLOCK] * full_blocks)
    blocks_widget.extend([INCOMPLETE_BLOCK_GRAD[0]] * empty_blocks)
    # marginal case - remainder due to how granular our blocks are
    remainder = perc - full_blocks*perc_per_block
    # epsilon needed for rounding errors (check would be != 0.)
    # based on reminder modify first empty block shading
    # depending on remainder
    if remainder > epsilon:
        grad_index = int((len(INCOMPLETE_BLOCK_GRAD) * remainder)/perc_per_block)
        blocks_widget[full_blocks] = INCOMPLETE_BLOCK_GRAD[grad_index]

    # build perc widget
    str_perc = '%.2f' % perc
    # -1 because the percentage sign is not included
    perc_widget = '[%s%%]' % str_perc.ljust(len(max_perc_widget) - 3)

    # form progressbar
    progress_bar = '%s%s%s' % (''.join(blocks_widget), separator, perc_widget)
    # return progressbar as string
    return ''.join(progress_bar)


def copy_progress(copied, total):
    print('\r' + progress_percentage(100*copied/total, width=30), end='')


def copyfile(src, dst, *, follow_symlinks=True):
    """Copy data from src to dst.

    If follow_symlinks is not set and src is a symbolic link, a new
    symlink will be created instead of copying the file it points to.

    """
    if shutil._samefile(src, dst):
        raise shutil.SameFileError("{!r} and {!r} are the same file".format(src, dst))

    for fn in [src, dst]:
        try:
            st = os.stat(fn)
        except OSError:
            # File most likely does not exist
            pass
        else:
            # XXX What about other special files? (sockets, devices...)
            if shutil.stat.S_ISFIFO(st.st_mode):
                raise shutil.SpecialFileError("`%s` is a named pipe" % fn)

    if not follow_symlinks and os.path.islink(src):
        os.symlink(os.readlink(src), dst)
    else:
        size = os.stat(src).st_size
        with open(src, 'rb') as fsrc:
            with open(dst, 'wb') as fdst:
                copyfileobj(fsrc, fdst, callback=copy_progress, total=size)
    return dst


def copyfileobj(fsrc, fdst, callback, total, length=16*1024):
    copied = 0
    while True:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)
        copied += len(buf)
        callback(copied, total=total)


def copy_with_progress(src, dst, *, follow_symlinks=True):
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    copyfile(src, dst, follow_symlinks=follow_symlinks)
    shutil.copymode(src, dst)
    return dst

def ver_modifcation():
    try:
        parser = ConfigParser()
        parser.read(update_ini)
        latest = float(parser.get('version', 'current'))
        parser = ConfigParser()
        parser.read(r'info\versioninfo.ini')
        parser.set('version', 'current', str(latest))
        with open(r'info\versioninfo.ini', 'w') as versionfile:
            parser.write(versionfile)
        messagebox.showinfo('Update Complete v{0}'.format(latest), 'Update complete, press OK to relaunch the application')
        subprocess.Popen(app_name)
    except Exception as e:
        messagebox.showwarning('Update Warning',f'Version file not could not be updated:\n\n{e}')

def ver_validate():
    try:
        parser = ConfigParser()
        parser.read(r'info\versioninfo.ini')
        global current
        current = float(parser.get('version', 'current'))
        parser.read(update_ini)
        global latest
        latest = float(parser.get('version', 'current'))
        if current >= latest:
            messagebox.showinfo('Update','No new update available')
            sys.exit()        
    except Exception as e:
        messagebox.showwarning('Update Warning',f'Program version could not be validated, please notify support@domain.com\n\n{e}')
        sys.exit()

def move():
    if not os.path.exists(r'info\old'):
        os.mkdir(r'info\old')
    if os.path.isfile(rf'info\old\{app_name}'):
        os.remove(rf'info\old\{app_name}')
    shutil.copy(app_name, rf'info\old\{app_name}') 
    
ver_validate()
move()
print(f'From: {src}\nTo: {dst}')
copy_with_progress(src, dst,follow_symlinks=True)
ver_modifcation()
sys.exit()
