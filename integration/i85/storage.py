"""Private I85 journal I/O. Residues are evidence, never rollback assertions."""
import json
import os
from pathlib import Path
import re
import stat
from uuid import uuid4
from local_admin import boundary as b


def checked(path,directory=False):
    b.private(path,directory)
    if not directory and Path(path).lstat().st_nlink!=1:raise b.Blocked('I85_CUSTODY_LINK_COUNT')


def sync_dir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)


def decode(raw):
    def unique(pairs):
        value={}
        for key,item in pairs:
            if key in value:raise ValueError('duplicate key')
            value[key]=item
        return value
    def constant(value):raise ValueError('nonfinite JSON')
    try:return json.loads(raw,object_pairs_hook=unique,parse_constant=constant)
    except (ValueError,UnicodeError):raise b.Blocked('I85_JOURNAL_INVALID') from None


def read(path):
    checked(path)
    try:return decode(Path(path).read_bytes())
    except (ValueError,UnicodeError):raise b.Blocked('I85_JOURNAL_INVALID') from None


def atomic_bytes(path,data):
    path=Path(path);checked(path.parent,True)
    # No collision with an old .next; admission checks still BLOCK on residue.
    temporary=path.with_name('.'+path.name+'.'+uuid4().hex+'.next')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,'wb') as out:out.write(data);out.flush();os.fsync(out.fileno())
        os.replace(temporary,path);sync_dir(path.parent)
    except BaseException:
        # A failed write is evidence too. Admission blocks until explicit repair.
        raise


def atomic_save(path,value):
    atomic_bytes(path,json.dumps(value,sort_keys=True,separators=(',',':')).encode()+b'\n')


def residues(directory):
    result=[]
    for p in Path(directory).iterdir():
        if p.name.endswith('.next'):
            if not re.fullmatch(r'(?:\.(?:state|secrets|lab|recovery|disposal|proof)\.json\.[a-f0-9]{32}|(?:state|secrets|lab|recovery|disposal|proof)\.json)\.next',p.name):raise b.Blocked('I85_UNKNOWN_RESIDUE')
            checked(p);result.append(p)
    return sorted(result)


def archive(directory,paths):
    destination=Path(directory)/'evidence'
    if not destination.exists():destination.mkdir(mode=0o700);sync_dir(directory)
    checked(destination,True)
    result={}
    for source in paths:
        checked(source)
        # Copy exact bytes before any repair; no material ever leaves custody.
        target=destination/(uuid4().hex+'-'+source.name)
        result[source.name]={'file':target.name,'sha256':b.digest(source.read_bytes())}
        fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as out:out.write(source.read_bytes());out.flush();os.fsync(out.fileno())
    sync_dir(destination);sync_dir(directory)
    return result


def remove_private_tree(path):
    # Only the owned private custody tree; no symlink traversal or broad chmod.
    path=Path(path);checked(path,True)
    for p in path.iterdir():
        if p.is_dir() and not p.is_symlink():remove_private_tree(p)
        else:checked(p);p.unlink()
    sync_dir(path);path.rmdir();sync_dir(path.parent)
