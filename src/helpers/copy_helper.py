import os

#Get all the steps required to copy pc_path to mcu_path, be it a folder or a file
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
            if d.startswith('.git') or d == '__pycache__' or d.startswith('.ipynb'):
                ignore_dirs.append(os.path.join(root,d))
                continue
            cc_path = os.path.normpath('/'.join((c_path,d))).replace(os.sep,'/')
            if cc_path in mcu_tree:
                continue
            ret.append([None,cc_path])
            mcu_tree.append(cc_path)
        for f in files:
            if f.startswith('.git') or f.endswith('~') or f.endswith('.bak') or f.endswith('.pyc') or f.endswith('.swp'):
                continue
            cc_path = '/'.join((c_path,f))
            ret.append([os.path.join(root,f).replace(os.sep,'/'),cc_path])
    return ret
    
