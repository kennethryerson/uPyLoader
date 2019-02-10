import os

#Get all the steps required to copy pc_path to mcu_path, be it a folder or a file
def can_ignore(file_name):
    ret = False
    if file_name.startswith('.git') or file_name.endswith('~') or file_name[:-1].endswith('.sw') or \
           file_name.endswith('.bak') or file_name.endswith('.pyc') or \
           file_name == '__pycache__' or file_name.startswith('.ipynb'):
        ret = True
    return ret

def copy_steps(pc_path,mcu_path):
    ret = []
    ignore_dirs = []
    mcu_tree = []
    pc_path = os.path.normpath(pc_path)
    _,dest = os.path.split(pc_path)
    
    if os.path.isfile(pc_path):
        cc_path = os.path.normpath('/'.join((mcu_path,dest))).replace(os.sep,'/')
        return [[pc_path,cc_path]]
    
    for root, dirs, files in os.walk(pc_path):
        skip = False
        for idir in ignore_dirs:
            if root.startswith(idir):
                skip = True
                break
        if skip:
            continue
        c_path = os.path.normpath('/'.join((mcu_path,dest,root.replace(pc_path,'')))).replace(os.sep,'/')
        for d in ['']+dirs:
            if can_ignore(d):
                ignore_dirs.append(os.path.join(root,d))
                continue
            cc_path = os.path.normpath('/'.join((c_path,d))).replace(os.sep,'/')
            if cc_path in mcu_tree:
                continue
            ret.append([None,cc_path])
            mcu_tree.append(cc_path)
        for f in files:
            if can_ignore(f):
                continue
            cc_path = '/'.join((c_path,f))
            ret.append([os.path.join(root,f).replace(os.sep,'/'),cc_path])
    return ret
    
