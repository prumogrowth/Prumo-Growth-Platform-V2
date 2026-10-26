/**
 * Disposable, single-process test adapter ONLY. Not an S0 database or installer.
 * Mutex serializes a MODEL; no PostgreSQL row-lock/S1 claim is made.
 */
import {mkdir,open,readFile,rename,unlink} from 'node:fs/promises';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';

class Serial {
  tail=Promise.resolve();
  async serial(fn) {
    let release;
    const previous=this.tail;
    this.tail=new Promise(r=>{release=r;});
    await previous;
    try {return await fn();} finally {release();}
  }
}
export class MemoryStore extends Serial {
  durable=false;
  constructor(seed,{hook=async()=>{}}={}) {
    super(); this.state=structuredClone(seed); this.hook=hook;
  }
  async transact(fn) {
    return this.serial(async()=>{
      const next=structuredClone(this.state);
      const result=await fn(next);
      await this.hook('before_commit',next,result);
      this.state=next;
      await this.hook('after_commit',next,result);
      return result;
    });
  }
}
export class FileStore extends Serial {
  durable=true;
  constructor(directory,{hook=async()=>{}}={}) {
    super();
    if (!directory.includes('meta-s0-lab-')) throw Error('DISPOSABLE_DIRECTORY_REQUIRED');
    this.directory=directory;this.file=join(directory,'state.json');this.hook=hook;
  }
  async initialize(seed) {
    await mkdir(this.directory,{recursive:true,mode:0o700});
    // Exclusive seed; restart MUST use the existing state, never overwrite it.
    try {await readFile(this.file);throw Error('ALREADY_INITIALIZED');}
    catch(e){if(e.code!=='ENOENT')throw e;}
    await this.persist(seed);
  }
  async persist(state) {
    const temp=join(this.directory,randomUUID()+'.tmp');
    let handle;
    try {
      await this.hook('before_write',state);
      handle=await open(temp,'wx',0o600);
      await handle.writeFile(JSON.stringify(state),'utf8');
      await this.hook('before_file_sync',state);
      await handle.sync();
      await handle.close();handle=null;
      await this.hook('before_rename',state);
      await rename(temp,this.file);
      await this.hook('after_rename',state);
      const directory=await open(this.directory,'r');
      try {await directory.sync();} finally {await directory.close();}
      await this.hook('after_directory_sync',state);
    } finally {
      if(handle)await handle.close();
      await unlink(temp).catch(e=>{if(e.code!=='ENOENT')throw e;});
    }
  }
  async snapshot() {return JSON.parse(await readFile(this.file,'utf8'));}
  async transact(fn) {
    return this.serial(async()=>{
      const next=await this.snapshot();
      const result=await fn(next);
      await this.persist(next);
      await this.hook('after_commit_before_return',next,result);
      return result;
    });
  }
}
