# Experimental worker artifact recipe v1: source contract

Refs #25 D04.01/.02/.04; #31 D09.03/.05 supporting; #21.
Base accepted main752e0b06/PR375. SOURCE ONLY / UNRUN; all finite grants SPENT.

## Small next step, not build authority

The [accepted artifact plan](D04_AUTHOR_WORKER_ARTIFACT_PLAN_2026-10-31.md)
requires an explicitly new, bounded six-child compile/link/MT comparison using
reused dependencies. PR375 binds historical metadata, not live file freshness
or selected link closure. Freeze the literal argument recipe as testable data
before a future effectful coordinator. Do not execute strings from old manifests.

Root read ONLY frozen D: build.ninja/rules.ninja TEXT. Historical C: compatibility
paths and wrapper commands remain historical, never executed or recreated.
Selected effective flags/order below preserve their nonincremental semantics;
new experimental definition and explicit owned output names are intentional.
No source/header/library/tool/SDK payload was newly read, built or executed.

Root initially owns this NEW contract, then NEW
`native/llama-worker/worker_artifact_recipe_v1.mjs`. Independent author first
freezes NEW `worker_artifact_recipe_v1_first.mjs` on separate serialized branch
BEFORE producer; reviewers read only. No other source path/normal worker/profile
or dependency changes. Coordinator owns integration/shared checkout mutations.

## One pure interface

Export ONLY `planWorkerArtifactComparisonV1(config)`, synchronous pure data.
No filesystem/environment/process/network/evaluation imports or callbacks.
config exact plain/null-prototype enumerable own-data keys ONLY compiler,linker,
manifestTool,workerRoot,upstreamA,upstreamB,buildA,buildB,targetRoot,sdkUmRoot.
All primitive strings; reject accessors/symbols/extras/boxed/coerced values
without invoking getters. Errors ONLY `WorkerArtifactRecipeV1Invalid` for
shape/path/semantics and `WorkerArtifactRecipeV1Limit` for string/argv byte-size
limits. No actual path, command or OS error text in exceptions.

Input paths are CANONICAL LEXICAL forward-slash Windows absolute paths: uppercase
D:/ for worker/upstream/build/target roots; tools/sdkUmRoot may use uppercase
C:/ or D:/ installed locations. No UNC/device path, backslash, empty/trailing
component, root-only drive, dot/dotdot component, trailing space/dot component,
control/DEL, quote, wildcard, colon after drive, equals/comma/semicolon/hash,
backtick or shell operators < > | &. Spaces/non-ASCII are permitted otherwise.
String UTF8<=1024B inclusive; each component<=255 UTF8 bytes. Limit violations
are Limit; forbidden syntax Invalid. This is lexical validation ONLY: ordinary
canonical containment/tool identity must be freshly proven by future admission.

Tool leaf names EXACT cl.exe/link.exe/mt.exe respectively (case-sensitive recipe).
workerRoot,upstreamA/B,buildA/B,targetRoot must be pairwise DISTINCT and disjoint
under Windows case-insensitive component containment. Prefix peers such as
D:/tree and D:/tree-other are disjoint. sdkUmRoot must not overlap any project
root; tools must not be inside any project root. No silent normalization,
case folding or source/output relocation in emitted strings.

## Closed output, six steps and explicit owned names

Return deeply frozen detached plain data with EXACT keys/order version,kind,
purpose,qualified,linkQualification,closureComplete,requiresFreshAdmission,
normalWorkerUnchangedRequired,candidates,steps. version1,kind
worker_artifact_recipe_v1,purpose experimental_worker_artifact_only;
three qualification flags false, both requirement flags true.

Exactly candidates A then B. Each EXACT keys/order id,upstreamRoot,
dependencyBuildRoot,outputRoot,object,executable,preEmbedCopy,manifest,
compilerPdb,linkerPdb,importLibrary. outputRoot = targetRoot +
/worker-author-b2-candidate-a or -b. Fixed leaves main.cpp.obj,
locallore-author-worker.exe,locallore-author-worker.pre-embed.exe,
locallore-author-worker.exe.manifest,compile.pdb,link.pdb,
locallore-author-worker.lib. No normal packaged worker/profile name or overwrite
permission. Describe fresh exclusive paths only; do not create them here.

steps exactly compile/link/manifest for A, then compile/link/manifest for B.
Each EXACT keys/order index,candidate,stage,tool,cwd,args,requiresPreEmbedCopy.
index0..5; stage compile/link/manifest. cwd always workerRoot. Tool is exact
respective supplied compiler/linker/manifestTool. args a dense string array,
no shell/wrapper/response-file or caller flag injection. requiresPreEmbedCopy
true ONLY for manifest; future coordinator must exclusively copy linked PE
to the declared preEmbedCopy and verify equality before MT can mutate it.
No copy/file execution is performed or authorized by these descriptors.

Compile argv, EXACT order (each bracket denotes one array element):

[/nologo,/TP,-DGGML_USE_CPU,/DLOCALLORE_INITIAL_WORLD_EXPERIMENTAL_V1=1],
then FIVE [-I<include>] elements preserving frozen raw aliases under that
candidate's upstreamRoot: /common/., /vendor/nlohmann/..,
/vendor/sheredom/.., /src/../include, /ggml/src/../include.
These generated constant dot aliases preserve the historical recipe; they
are not accepted from config or proof of actual canonical identity.
Then [/DWIN32,/D_WINDOWS,/EHsc,/O2,/Ob2,/DNDEBUG,-MD,/Brepro,
/experimental:deterministic], SIX pathmap elements, [-std:c++17,/showIncludes,
/Fo<object>,/Fd<compilerPdb>,/FS,-c,main.cpp].

Pathmaps: for workerRoot/upstreamRoot/outputRoot in that order, emit TWO
/pathmap:<source>=<virtual> arguments each: source as supplied forward slashes,
then with ALL slashes replaced by backslashes. Virtual identities EXACT
X:\locallore\worker, X:\locallore\llama, X:\locallore\build, respectively.
Do not include shell quote characters inside any argument. Literal main.cpp
is relative to freshly validated workerRoot, not a caller filename.

Link argv, EXACT order: [/nologo,<object>,/out:<executable>,
/implib:<importLibrary>,/pdb:<linkerPdb>,/version:0.0,/machine:x64,
/INCREMENTAL:NO,/subsystem:console,/Brepro,/MANIFEST,
/MANIFESTFILE:<manifest>], then SEVEN archives under dependencyBuildRoot:
llama/common/llama-common.lib, llama/src/llama.lib, llama/ggml/src/ggml.lib,
llama/ggml/src/ggml-cpu.lib, llama/ggml/src/ggml-base.lib,
llama/common/llama-common-base.lib, llama/vendor/cpp-httplib/cpp-httplib.lib.
Then TEN absolute SDK arguments under sdkUmRoot, names in order kernel32.lib,
user32.lib,gdi32.lib,winspool.lib,shell32.lib,ole32.lib,oleaut32.lib,uuid.lib,
comdlg32.lib,advapi32.lib. Effective DEFAULTLIB/CRT/search resolution remains
a FUTURE guarded input prerequisite; this list is not complete selected closure.
No NODEFAULTLIB, replacement libs, LINKREPRO, incremental/user manifest mode,
MANIFEST:NO/EMBED substitution, CMake/Ninja/cmd wrapper or RC stage.

Manifest argv EXACT [/nologo,/manifest,<manifest>,
/outputresource:<executable>;#1]. Last value is ONE literal argv element;
semicolon/hash are generated constant syntax, not accepted caller characters.
Future native ProcessStartInfo.ArgumentList must preserve element boundaries;
a pure/headless test is not native argv/MT execution evidence.

For each step bound sum of UTF8 byte lengths of all args plus3 per element
<=24576B. This is a conservative argument-data bound, not a proven Windows
process command-line encoder bound or native launch qualification. Reject excess
Limit, never omit flags/arguments. Whole output JSON UTF8<=65536B, otherwise
Limit; no partial output/truncation. Caller mutations/repeated calls cannot
alter previous output or shared state.

## Independent FIRST and future gate

Independent export `runWorkerArtifactRecipeSelfchecksV1(api)` takes ONLY
{planWorkerArtifactComparisonV1}. Synthetic path data, no real FS/native tools.
Exactly16 groups R01..R16; finite six-key summary version1,kind
worker_artifact_recipe_first_v1,executed/passed16,failed0,emptyfailed_case_ids
is the sole success. Missing API is UNRUN_SETUP, never passing RED.

R01 closed config/no getters/symbol/coercion; R02 tool/drive/leaf rules;
R03 unsafe lexical/ADS/UNC/dot/wildcard/control/delimiter refusal;
R04 case-insensitive containment/disjoint prefix peers;
R05 exact output/six-step order/flags; R06 complete compile literal order;
R07 five raw include aliases; R08 archive+SDK path/order and A/B source choice;
R09 exact nonincremental manifest link flags; R10 MT single ;#1 element/noRC;
R11 owned distinct output/PE-copy/PDB/implib roster;
R12 exact-inclusive1024B path/255B component and+1 byte refusals plus bounded
argv/output; R13 BOTH slash pathmap identities/order;
R14 copy/freeze/pure repeated calls; R15 no extra mode/flags/arbitrary command;
R16 no normal worker/profile adoption and requires-fresh/unqualified flags.
Keep every assertion; fixtures<128KiB/group. All SOURCE ONLY/UNRUN.

Next code packet should run only new recipe16 and unchanged binder16 as relevant
compatibility checks; no need to rerun unrelated244 binary-reader cases whose
source/interfaces do not change. Exact finite whole programs/retention reserve,
reviews and fresh inventory precede separate owner execution authority. Current
metadata2743728/cap2863104B,119376B free; no cap increase/reset/deletion assumed.

Future effectful coordinator still requires fresh fixed source/header/dependency
and ALL SDK/tool bytes, environment/root/search/no-shadow checks, new object
DEFAULTLIB validation, bounded output/temp roster, deadlines/closure and owned
path/storage admission BEFORE any compiler/linker/MT process. This pure recipe
does not implement or grant those effects. Original4GiB target and64MiB group/
724MiB joint/576KiB old records/8MiB fixtures remain unchanged. No SDK payload,
build/link/worker/model/app/device/OS/download/settings/release/desktop control
or automatic retry. Full D04/D09/desktop/human-quality gates open; AuthorDisabled.
