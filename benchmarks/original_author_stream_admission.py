"""Pure fixed read-only pre-transfer shell recipe and bounded evidence decoder. No dispatch."""
import re
import shlex

APP='org.locallore.app.litertverify'
TEST=APP+'.test'
MODEL_BYTES=2588147712
RESERVE=2*1024**3
MEMORY=4*1024**3
MAX_BYTES=16384
FIELDS=('BOOT','SDK','ABI','QEMU','USER','APP_PATH','TEST_PATH','APP_SHA256','TEST_SHA256')

class BatchRefused(RuntimeError):pass
def need(value,reason):
 if not value:raise BatchRefused(reason)
def identities(uids,hashes):
 need(type(uids) is dict and set(uids)=={APP,TEST} and all(type(x) is int and 10000<=x<2**31 for x in uids.values())
  and uids[APP]!=uids[TEST],'expected_uids')
 need(type(hashes) is dict and set(hashes)=={APP,TEST} and all(type(x) is str and re.fullmatch('[0-9a-f]{64}',x) for x in hashes.values()),'expected_hashes')
def safe_path(value):
 return type(value) is str and len(value)<=512 and re.fullmatch(r'/data/app/[A-Za-z0-9_~=/.-]+/base\.apk',value) is not None and '..' not in value and '//' not in value
def script(uid_app,uid_test,product_sha,test_sha):
 identities({APP:uid_app,TEST:uid_test},{APP:product_sha,TEST:test_sha})
 forward=f'package:{APP} uid:{uid_app}\npackage:{TEST} uid:{uid_test}'
 reverse=f'package:{TEST} uid:{uid_test}\npackage:{APP} uid:{uid_app}'
 lines=['export LC_ALL=C',
  'packages=$(cmd package list packages -U --user 0 '+shlex.quote(APP)+') || exit 1',
  'test "$packages" = '+shlex.quote(forward)+' || test "$packages" = '+shlex.quote(reverse)+' || exit 1',
  'app_line=$(cmd package path --user 0 '+shlex.quote(APP)+') || exit 1',
  'test_line=$(cmd package path --user 0 '+shlex.quote(TEST)+') || exit 1']
 for name in ('app','test'):
  lines.extend(['case "$'+name+'_line" in package:/data/app/*/base.apk) ;; *) exit 1;; esac',
   name+'_path=${'+name+'_line#package:}',
   'case "$'+name+'_path" in *[!A-Za-z0-9_~=/.-]*|*..*|*//*) exit 1;; esac',
   name+'_sum=$(sha256sum "$'+name+'_path") || exit 1',name+'_sha=${'+name+'_sum%% *}'])
 lines.extend(['test "$app_sha" = '+shlex.quote(product_sha)+' && test "$test_sha" = '+shlex.quote(test_sha)+' || exit 1',
  "printf 'BATCH_V1_BEGIN\\n'",
  "printf 'BOOT=%s\\n' \"$(getprop sys.boot_completed)\"",
  "printf 'SDK=%s\\n' \"$(getprop ro.build.version.sdk)\"",
  "printf 'ABI=%s\\n' \"$(getprop ro.product.cpu.abi)\"",
  "printf 'QEMU=%s\\n' \"$(getprop ro.kernel.qemu)\"",
  "printf 'USER=%s\\n' \"$(am get-current-user)\"",
  "printf 'APP_PATH=%s\\nTEST_PATH=%s\\nAPP_SHA256=%s\\nTEST_SHA256=%s\\n' \"$app_path\" \"$test_path\" \"$app_sha\" \"$test_sha\"",
  "printf 'PACKAGES_V1_BEGIN\\n%s\\nPACKAGES_V1_END\\nRESOURCES_V1_BEGIN\\n' \"$packages\"",
  'df -k /data || exit 1','cat /proc/meminfo || exit 1',"printf 'RESOURCES_V1_END\\nBATCH_V1_END\\n'"])
 return '\n'.join(lines)

def resource(lines,missing_bytes):
 need(type(missing_bytes) is int and 0<=missing_bytes<=2*MODEL_BYTES,'missing_bytes')
 need(len(lines)>=3 and lines[0].split()==['Filesystem','1K-blocks','Used','Available','Use%','Mounted','on'],'resource_header')
 df=lines[1].split()
 need(len(df)==6 and re.fullmatch('/dev/[A-Za-z0-9_/.-]+',df[0]) is not None
  and all(re.fullmatch('[0-9]{1,20}',x) is not None for x in df[1:4])
  and re.fullmatch('[0-9]{1,3}%',df[4]) is not None and int(df[4][:-1])<=100
  and df[5] in ('/data','/data/user/0') and int(df[2])<=int(df[1]) and int(df[3])<=int(df[1]),'resource_disk')
 rows={}
 for line in lines[2:]:
  match=re.fullmatch(r'([A-Za-z][A-Za-z0-9_()]*):\s+([0-9]+)( kB)?',line)
  need(match is not None and match[1] not in rows,'resource_rows')
  need(len(match[2])<=20,'resource_integer_bounds');rows[match[1]]=(int(match[2]),match[3])
 need('MemAvailable' in rows and rows['MemAvailable'][1]==' kB','resource_memory')
 free=int(df[3])*1024;memory=rows['MemAvailable'][0]*1024
 need(free>=missing_bytes+RESERVE and memory>=MEMORY,'target_capacity')
 return dict(source='/proc/meminfo',memory_available_bytes=memory,low_memory=None,free_bytes=free,missing_bytes=missing_bytes,reserve_bytes=RESERVE)

def decode(raw,expected_uids,expected_hashes,missing_bytes):
 identities(expected_uids,expected_hashes)
 need(type(raw) is bytes and 0<len(raw)<=MAX_BYTES,'raw_bounds')
 try:text=raw.decode('ascii')
 except UnicodeError:raise BatchRefused('raw_ascii') from None
 text=text.replace('\r\n','\n');need('\r' not in text,'bare_cr')
 if text.endswith('\n'):text=text[:-1]
 lines=text.split('\n');need(len(lines)>=20 and lines[0]=='BATCH_V1_BEGIN' and lines[-1]=='BATCH_V1_END','framing')
 values={}
 for line,key in zip(lines[1:10],FIELDS):
  need(line.startswith(key+'=') and key not in values,'field_order');values[key]=line[len(key)+1:]
 need(lines[10]=='PACKAGES_V1_BEGIN' and lines[13]=='PACKAGES_V1_END' and lines[14]=='RESOURCES_V1_BEGIN'
  and lines[-2]=='RESOURCES_V1_END','framing')
 need([values[k] for k in FIELDS[:5]]==['1','35','x86_64','1','0'],'profile')
 uids={}
 for line in lines[11:13]:
  row=re.fullmatch(r'package:([^\s]+) uid:([1-9][0-9]*)',line)
  need(row is not None and row[1] in (APP,TEST) and row[1] not in uids,'package_rows')
  need(len(row[2])<=10,'package_integer_bounds');uids[row[1]]=int(row[2])
 need(uids==expected_uids,'package_uids')
 packages={}
 for name,key in ((APP,'APP'),(TEST,'TEST')):
  path=values[key+'_PATH'];sha=values[key+'_SHA256']
  need(safe_path(path),'apk_path');need(sha==expected_hashes[name],'apk_hash')
  packages[name]=dict(uid=uids[name],path=path,sha256=sha)
 need(packages[APP]['path']!=packages[TEST]['path'],'apk_path_alias')
 resources=resource(lines[15:-2],missing_bytes)
 return dict(version=1,scope='real_author_stream_pretransfer_batch_v1',properties=dict(boot_completed='1',api='35',abi='x86_64',qemu='1'),
  current_user=0,packages=packages,resources=resources)
