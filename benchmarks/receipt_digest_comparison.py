"""Frozen synthetic stream-hash comparison; no production changes or real tool data."""
import argparse,functools,hashlib,json,os,statistics,subprocess,sys,time
from pathlib import Path
os.environ.update(TEMP='D:/Dev/_Temp',TMP='D:/Dev/_Temp',TMPDIR='D:/Dev/_Temp')
sys.dont_write_bytecode=True
R=Path.cwd()
GO=b'LL_STREAM_HASH_COMPARISON_V1\n'
IDS=['baseline_read_1m','readinto_64k','readinto_256k','readinto_1m','stdlib_file_digest']
LARGE=[('qemu',50887776,1),('adb',8273560,4),('dll',6785760,2),('emulator',1823328,1),('exe',106208,2)]
SMALL=[0,256,1024,4096,8192,16384,32768,65536]*4
PATTERN=bytes((73*i+19)%256 for i in range(256))
class Policy:
    def __init__(self):self.events=[]
    def audit(self,event,args):
        paths=list(args[:1]) if event in ('open','os.listdir','os.scandir','os.mkdir','os.remove','os.rmdir','os.truncate','os.chmod','os.utime') else list(args[:2]) if event in ('os.rename','os.link','os.symlink') else []
        for p in paths:
            if isinstance(p,(str,bytes)):
                text=os.path.normcase(os.path.abspath(os.fsdecode(p)));blocked=os.path.normcase(os.path.abspath('D:/Dev/_Migration'))
                if text==blocked or text.startswith(blocked+os.sep):self.events.append(dict(event=event,path=text,reason='migration_denied'));raise PermissionError('migration_denied')
        writes=[]
        if event=='open':
            path,mode,flags=args
            if (isinstance(mode,str) and any(x in mode for x in ('w','a','x','+'))) or (type(flags)is int and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):writes=[path]
        elif event in ('os.mkdir','os.remove','os.rmdir','os.truncate','os.chmod','os.utime'):writes=list(args[:1])
        elif event in ('os.rename','os.link','os.symlink'):writes=list(args[:2])
        for p in writes:
            if isinstance(p,(str,bytes)) and os.fsdecode(p)!=os.devnull and Path(os.path.abspath(os.fsdecode(p))).drive.upper()!='D:':self.events.append(dict(event=event,path=os.fsdecode(p),reason='write_requires_D'));raise PermissionError('write_requires_D')
POLICY=Policy();sys.addaudithook(POLICY.audit)
sys.path.insert(0,str(R))
from benchmarks import receipt_avd_environment as e
from benchmarks.windows_tcp_control import validate_output

def need(value,reason):e.require(value,reason)
def sources():
    names=subprocess.run(['git','-c','gc.auto=0','ls-files','-z'],cwd=R,check=True,capture_output=True,timeout=10).stdout.decode().split('\0')
    return {n:e.digest(R/n)for n in names if n}
def context():
    need(subprocess.run(['git','status','--porcelain'],cwd=R,check=True,capture_output=True,timeout=10).stdout==b'','dirty_source')
    return subprocess.run(['git','rev-parse','HEAD'],cwd=R,check=True,capture_output=True,timeout=10).stdout.decode().strip()
def tools():
    paths=[Path(sys.executable),Path(hashlib.__file__)]
    dll=Path(sys.executable).parent/('python%d%d.dll'%sys.version_info[:2])
    if dll.exists():paths.append(dll)
    return [e.binding(p)for p in sorted(paths)]
def protocol(pin):
    value=e.read_bound_json(pin['path'],pin['sha256']);e.check_binding(pin)
    need(value['version']==1 and value['scope']=='stream-hash-comparison-v1' and value['methods']==IDS and value['small_sizes']==SMALL and value['large_files']==[dict(name=n,bytes=s,weight=w)for n,s,w in LARGE] and value['weighted_order']==['qemu','adb','dll','emulator','exe','adb','dll','exe','adb','adb'] and value['round_orders']==[IDS[i:]+IDS[:i]for i in range(5)] and value['warmup_order']==IDS and value['owner_seconds']==180,'protocol')
    return value

def logical_chunk(offset,length):
    start=offset%len(PATTERN);return (PATTERN*((start+length+255)//256))[start:start+length]
def expected(size):
    h=hashlib.sha256();offset=0
    while offset<size:
        n=min(65521,size-offset);h.update(logical_chunk(offset,n));offset+=n
    return h.hexdigest()
def corpus(out):
    root=out/'corpus';root.mkdir();(root/'large').mkdir();(root/'small').mkdir()
    specs=[('large/'+name+'.bin',size)for name,size,_ in LARGE]+[('small/source-%03d.bin'%i,size)for i,size in enumerate(SMALL)]
    result={}
    for relative,size in specs:
        p=root/relative;offset=0
        with p.open('xb')as f:
            while offset<size:
                n=min(1024*1024,size-offset);block=logical_chunk(offset,n);need(f.write(block)==n,'write');offset+=n
            f.flush();os.fsync(f.fileno())
        result[relative]=dict(path=str(p),bytes=size,sha256=expected(size))
    need(sum(x['bytes']for x in result.values())==68389656,'corpus_size');return result

def independent_disk(mapping):
    result={}
    for name,pin in mapping.items():
        p=e.safe_path(pin['path']);raw=p.read_bytes();actual=dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());need(actual==pin,'corpus_changed');result[name]=actual
    return result

def readinto(path,size):
    p=e.safe_path(path)
    h=hashlib.sha256();buffer=bytearray(size);view=memoryview(buffer)
    with p.open('rb')as f:
        while True:
            count=f.readinto(buffer)
            e.require(type(count)is int and 0<=count<=len(buffer),'invalid_hash_read')
            if count==0:break
            h.update(view[:count])
    return h.hexdigest()
def file_digest(path):
    p=e.safe_path(path)
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run_method(name,order,mapping):
    functions={'baseline_read_1m':e.digest,'readinto_64k':functools.partial(readinto,size=65536),'readinto_256k':functools.partial(readinto,size=262144),'readinto_1m':functools.partial(readinto,size=1048576),'stdlib_file_digest':file_digest}
    fn=functions[name];large=[]
    for item in order:
        pin=mapping['large/'+item+'.bin'];start=time.perf_counter_ns();actual=fn(Path(pin['path']));elapsed=time.perf_counter_ns()-start
        need(elapsed>=0 and actual==pin['sha256'],'measured_hash_or_clock');large.append(dict(file=item,wall_ns=elapsed,sha256=actual))
    small=[mapping['small/source-%03d.bin'%i]for i in range(len(SMALL))]
    start=time.perf_counter_ns();actual=[fn(Path(pin['path']))for pin in small];small_ns=time.perf_counter_ns()-start
    need(small_ns>=0 and actual==[p['sha256']for p in small],'small_hash_or_clock')
    return dict(method=name,weighted_calls=large,weighted_ns=sum(p['wall_ns']for p in large),weighted_bytes=99589280,small_batch_ns=small_ns,small_files=len(small),small_bytes=513024)

def worker(out,sha):
    need(sys.stdin.buffer.read(len(GO))==GO,'barrier');q=e.read_bound_json(out/'request-v1.json',sha)
    need(sys.version_info[:3]==(3,14,7),'python_version');spec=protocol(q['protocol'])
    need(q['runner']==e.binding(Path(__file__)) and q['sources']==sources() and q['head']==context()==spec['baseline_commit'] and q['tools']==tools(),'inputs_changed')
    until=time.monotonic()+5
    while not(out/'started-v1.json').exists()and time.monotonic()<until:time.sleep(.01)
    started=e.read_json(out/'started-v1.json');need(started['worker']==e.process_identity(os.getpid())and started['request']==e.binding(out/'request-v1.json'),'started')
    samples=[];mapping=None;passed=False;reason=None
    try:
        mapping=corpus(out);e.create_json(out/'corpus-expected-v1.json',mapping);before=independent_disk(mapping);e.create_json(out/'corpus-before-v1.json',before)
        with(out/'samples-v1.jsonl').open('xb')as raw:
            for round_index,order in [(-1,spec['warmup_order'])]+list(enumerate(spec['round_orders'])):
                for name in order:
                    row=run_method(name,spec['weighted_order'],mapping);row.update(round=round_index,warmup=round_index==-1);samples.append(row);encoded=e.encoded(row);need(raw.write(encoded)==len(encoded),'sample_write');raw.flush();os.fsync(raw.fileno())
        after=independent_disk(mapping);e.create_json(out/'corpus-after-v1.json',after)
        need(sorted(p.relative_to(out/'corpus').as_posix()for p in(out/'corpus').rglob('*')if p.is_file())==sorted(mapping),'corpus_roster')
        need(q['runner']==e.binding(Path(__file__))and q['sources']==sources()and q['tools']==tools()and q['head']==context()and not POLICY.events,'final_inputs_or_policy')
        medians={name:dict(weighted_ns=statistics.median(x['weighted_ns']for x in samples if x['method']==name and not x['warmup']),small_batch_ns=statistics.median(x['small_batch_ns']for x in samples if x['method']==name and not x['warmup']))for name in IDS}
        base=medians[IDS[0]];qualifiers=[]
        for name in IDS[1:]:
            row=medians[name];row.update(weighted_change_percent=100*(row['weighted_ns']/base['weighted_ns']-1),small_change_percent=100*(row['small_batch_ns']/base['small_batch_ns']-1),production39_eligible=name!='stdlib_file_digest')
            row['qualifies']=row['production39_eligible']and row['weighted_ns']*100<=base['weighted_ns']*95 and row['small_batch_ns']*100<=base['small_batch_ns']*110
            if row['qualifies']:qualifiers.append(name)
        qualifiers.sort(key=lambda name:(medians[name]['weighted_ns'],medians[name]['small_batch_ns'],IDS.index(name)))
        e.create_json(out/'comparison-v1.json',dict(version=1,scope=spec['scope'],medians=medians,qualifying_candidates=qualifiers,production_changed=False,feature_acceptance=False));passed=True
    except BaseException as error:
        reason=type(error).__name__
        raise
    finally:
        e.create_json(out/'worker-result-v1.json',dict(version=1,passed=passed,reason=reason,completed_samples=len(samples),expected_samples=30,policy_attempts=POLICY.events,feature_acceptance=False))
    return 0

def main():
    if sys.argv[1:2]==['_worker']:return worker(Path(sys.argv[2]),sys.argv[3])
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--protocol',required=True,type=Path);parser.add_argument('--protocol-sha256',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    need(os.name=='nt'and R.drive.upper()=='D:'and R.resolve(strict=True)==R,'host');pp=e.safe_path(args.protocol);need(pp.drive.upper()=='D:'and e.digest(pp)==args.protocol_sha256,'protocol_pin');pin=e.binding(pp);spec=protocol(pin);need(context()==spec['baseline_commit'],'head')
    out=validate_output(args.output);out.mkdir();q=dict(version=1,protocol=pin,runner=e.binding(Path(__file__)),head=context(),sources=sources(),tools=tools(),python=sys.version,seconds=180);e.create_json(out/'request-v1.json',q);request=e.binding(out/'request-v1.json')
    def started(child):
        e.create_json(out/'started.pending-v1.json',dict(worker=e.process_identity(child.pid),request=request));(out/'started.pending-v1.json').rename(out/'started-v1.json');return True
    owner=e.supervise([sys.executable,'-I','-S','-B',str(Path(__file__).resolve()),'_worker',str(out),request['sha256']],GO,out,180,started)
    e.create_json(out/'owner-result-v1.json',owner);after_sources=sources();after_tools=tools();e.create_json(out/'sources-after-v1.json',after_sources);e.create_json(out/'tools-after-v1.json',after_tools);stable=q['sources']==after_sources and q['runner']==e.binding(Path(__file__))and q['tools']==after_tools and q['head']==context();e.check_binding(pin)
    result=dict(version=1,passed=owner['status']=='child_exited'and owner['worker_returncode']==0 and owner['cleanup_complete']is True and owner['output_capture_complete']is True and owner['stderr_bytes']==0 and stable and not POLICY.events,owner=owner,sources_equal=stable,policy_attempts=POLICY.events,feature_acceptance=False)
    e.create_json(out/'result-v1.json',result);print(json.dumps(result,sort_keys=True));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
