# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
# Independent parent FIRST against the frozen fixed-two runtime contract.
# SOURCE ONLY / UNRUN. Definitions only: no top-level suite or producer call.
# JSON fixtures use synthetic identities; they attest no SDK file or payload.
function Invoke-FixedTwoParentSelfchecksV1($Dictionary, $ExpectedProofs) {
    $ErrorActionPreference = 'Stop'
    $utf8 = [Text.UTF8Encoding]::new($false)
    $profileId = 'msvc-library-metadata-v1'
    $priorNames = @('kernel32.lib','msvcprt.lib','msvcrt.lib','oldnames.lib','ucrt.lib','uuid.lib','vcomp.lib','vcruntime.lib','ws2_32.lib')
    $catalogNames = @('kernel32.lib','user32.lib','gdi32.lib','winspool.lib','shell32.lib','ole32.lib','oleaut32.lib','uuid.lib','comdlg32.lib','advapi32.lib','msvcprt.lib','msvcrt.lib','oldnames.lib','vcomp.lib','ws2_32.lib')
    $roots = @('root-0','root-1','root-2','root-3','root-4')
    $Roster = [ordered]@{search=[ordered]@{rootIdentities=$roots};sdkInputs=@(foreach($name in $catalogNames){[ordered]@{requestedName=$name}})}

    function ConvertTo-F2ParentJson($Value) {
        ConvertTo-Json -InputObject $Value -Depth 32 -Compress
    }
    function Copy-F2ParentData($Value) {
        ConvertFrom-Json -InputObject (ConvertTo-F2ParentJson $Value) -Depth 32 -AsHashtable
    }
    function Get-F2ParentDigest($Value) {
        [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($utf8.GetBytes((ConvertTo-F2ParentJson $Value)))).ToLowerInvariant()
    }
    function Assert-F2Parent($Condition) {
        if(-not $Condition){throw 'ParentFirstAssertion'}
    }
    function New-F2ParentGateSummary {
        # Match the live suite return type, not only its JSON reconstruction.
        [ordered]@{version=1;kind='fixed_two_parent_first_v1';executed=6;passed=6;failed=0;failed_case_ids=[string[]]@()}
    }
    function Assert-F2ParentGateSummaryInvalid($Value) {
        $caught=$false
        try{$null=Validate-FirstSummary $Value 6 'fixed_two_parent_first_v1'}catch{
            if(@('ReportKeys','ReportInteger','ObservationFirstSummary') -cnotcontains $_.Exception.Message){throw}
            $caught=$true
        }
        Assert-F2Parent $caught
    }
    function New-F2ParentContext {
        [ordered]@{cwdIdentity='cwd-1';cwdLibraryCount=0;rootIdentities=@($roots)}
    }
    function New-F2ParentRequest([int]$Index,[string]$Outcome='not_reached') {
        [ordered]@{slot=$Index+33;name=@('ucrt.lib','vcruntime.lib')[$Index];priorNameId=@(4,7)[$Index];requestedBySlot=29;outcome=$Outcome;candidate=$null;pin=$null;strict=$null;profile=$null}
    }
    function New-F2ParentMode([string[]]$Names) {
        $directives=@(foreach($name in $Names){'/DEFAULTLIB:' + $(if($name.Length -gt 255){$name.Substring(0,$name.Length-4)}else{$name})})
        [Array]::Sort($directives,[StringComparer]::Ordinal)
        $metadata=[ordered]@{objects=1;imports=0;directives=@($directives);defaultLibraries=@($Names)}
        $sections=if($Names.Count -eq 0){0}else{1}
        return ,@(0,1,0,$Names.Count,$Names.Count,$sections,0,0,0,(Get-F2ParentDigest $metadata))
    }
    function New-F2ParentReport([string[]]$Outcomes=@('selected','selected'),[string[]]$FirstNames=@(),[string[]]$SecondNames=@()) {
        [string[]]$left=@($FirstNames);[string[]]$right=@($SecondNames)
        [Array]::Sort($left,[StringComparer]::Ordinal);[Array]::Sort($right,[StringComparer]::Ordinal)
        $namesByRequest=@($left,$right)
        $requests=@();$probes=@();[long]$bytes=0;$inputs=0;$sections=0
        for($index=0;$index -lt 2;$index++){
            $request=New-F2ParentRequest $index $Outcomes[$index]
            if($Outcomes[$index] -eq 'missing'){
                for($rootIndex=0;$rootIndex -lt 5;$rootIndex++){$probes+=,[ordered]@{index=$index;rootIndex=$rootIndex;outcome='missing'}}
            }else{
                $mode=New-F2ParentMode $namesByRequest[$index]
                $size=20
                if($namesByRequest[$index].Count -gt 0){
                    $tokens=@(foreach($name in $namesByRequest[$index]){'/DEFAULTLIB:' + $(if($name.Length -gt 255){$name.Substring(0,$name.Length-4)}else{$name})})
                    $size=60+$utf8.GetByteCount(($tokens -join ' '))
                }
                $request.candidate=[ordered]@{index=$index;rootIndex=0;bytes=$size;rootIdentity=$roots[0];leafIdentity=('leaf-'+$index)}
                # Synthetic lowercase digests are schema data, not observed pins.
                $request.pin=[ordered]@{slot=$index+33;name=$request.name;rootIndex=0;bytes=$size;sha256=('b'*64);rootIdentity=$roots[0];leafIdentity=('leaf-'+$index)}
                $request.strict=@($mode);$request.profile=@($mode)
                $probes+=,[ordered]@{index=$index;rootIndex=0;outcome='selected'}
                $bytes+=$size;$inputs++;$sections+=2*$mode[5]
            }
            $requests+=,$request
        }
        $union=[Collections.Generic.SortedSet[string]]::new([StringComparer]::Ordinal)
        foreach($name in $priorNames){$null=$union.Add($name)}
        for($index=0;$index -lt 2;$index++){if($null -ne $requests[$index].profile){foreach($name in $namesByRequest[$index]){$null=$union.Add($name)}}}
        [string[]]$libraryNames=@($union)
        $provided=@();$allProvided=$true
        foreach($name in $libraryNames){
            $slot=$null;$old=[Array]::IndexOf([string[]]$catalogNames,$name)
            if($old -ge 0){$slot=$old+18}else{foreach($request in $requests){if($null -ne $request.pin -and $request.name -ceq $name){$slot=$request.slot}}}
            if($null -eq $slot){$allProvided=$false};$provided+=,$slot
        }
        $graphRows=@()
        for($index=0;$index -lt 2;$index++){
            $ids=$null
            if($null -ne $requests[$index].profile){$ids=@(foreach($name in $namesByRequest[$index]){[Array]::IndexOf($libraryNames,$name)})}
            $graphRows+=,[ordered]@{slot=$index+33;libraryIds=$ids}
        }
        [ordered]@{
            version=1;kind='fixed_two_runtime_metadata_v1';purpose='build_input_metadata_only'
            qualified=$false;linkQualification=$false;closureComplete=$false;captureComplete=$true;status='complete'
            selfchecks=[ordered]@{version=1;kind='fixed_two_runtime_first_v1';executed=24;passed=24;failed=0;failed_case_ids=@()}
            proofs=(Copy-F2ParentData $ExpectedProofs)
            search=[ordered]@{context=(New-F2ParentContext);probes=$probes;finalVerified=$true}
            job=[ordered]@{profileId=$profileId;inputCount=$inputs;inputBytes=$bytes;attempts=2*$inputs;sections=$sections;stopped=$false}
            io=[ordered]@{reservedInputs=$inputs;reservedBytes=$bytes;reservedReadBytes=2*$bytes;actualReadBytes=2*$bytes}
            requests=$requests
            facts=[ordered]@{libraryNames=$libraryNames;providedSlots=$provided;priorNameIds=@(foreach($name in $priorNames){[Array]::IndexOf($libraryNames,$name)});rows=$graphRows;bothProfileMetadataAvailable=($inputs -eq 2);allKnownNamesProvided=$allProvided}
            critical=$null
        }
    }
    function New-F2ParentStopped([string]$Critical='InputFailure') {
        $report=New-F2ParentReport @('missing','missing')
        $report.captureComplete=$false;$report.status='stopped';$report.critical=$Critical;$report.facts=$null
        $report.search=[ordered]@{context=$null;probes=@();finalVerified=$false}
        $report.requests=@((New-F2ParentRequest 0),(New-F2ParentRequest 1))
        return $report
    }
    function New-F2ParentPrefix([string]$Critical='RequestOrder') {
        $report=New-F2ParentStopped $Critical;$complete=New-F2ParentReport
        $report.search.context=New-F2ParentContext;$report.search.probes=@([ordered]@{index=0;rootIndex=0;outcome='selected'})
        $report.requests[0]=$complete.requests[0];$report.requests[0].profile=$null
        $report.job=[ordered]@{profileId=$profileId;inputCount=1;inputBytes=20;attempts=1;sections=0;stopped=$false}
        $report.io=[ordered]@{reservedInputs=1;reservedBytes=20;reservedReadBytes=40;actualReadBytes=40}
        return $report
    }
    function New-F2ParentGlobalStop {
        $report=New-F2ParentPrefix 'JobStopped'
        $report.requests[0].candidate.bytes=56;$report.requests[0].pin.bytes=56
        $site=[Array]::IndexOf([string[]]$Dictionary.sites,'metadata_job_sections')
        $report.requests[0].strict=@(1,3,$site,$null,$null,$null,4294967295,0,0,4294967295,2097152)
        $report.job=[ordered]@{profileId=$profileId;inputCount=1;inputBytes=56;attempts=1;sections=0;stopped=$true}
        $report.io=[ordered]@{reservedInputs=1;reservedBytes=56;reservedReadBytes=112;actualReadBytes=112}
        return $report
    }
    function Assert-F2ParentValid($Report) {
        $canonical=(ConvertTo-F2ParentJson $Report)+[string][char]10
        $raw=$utf8.GetBytes($canonical)
        Assert-F2Parent ($raw.Length -le 24576)
        $validated=Validate-FixedTwoRuntimeReport $raw $Dictionary $ExpectedProofs $Roster
        Assert-F2Parent ((ConvertTo-F2ParentJson $validated) -ceq (ConvertTo-F2ParentJson $Report))
    }
    function Assert-F2ParentRawInvalid([byte[]]$Raw) {
        $caught=$false
        try{$null=Validate-FixedTwoRuntimeReport $Raw $Dictionary $ExpectedProofs $Roster}catch{
            if($_.Exception.Message -cne 'InvalidRuntimeMetadataReport'){throw}
            $caught=$true
        }
        Assert-F2Parent $caught
    }
    function Assert-F2ParentInvalid($Report) {
        Assert-F2ParentRawInvalid ($utf8.GetBytes((ConvertTo-F2ParentJson $Report)+[string][char]10))
    }
    function New-F2ParentLongNames([int]$Count) {
        return ,@(for($index=0;$index -lt $Count;$index++){$index.ToString('00')+'-'+('a'*252)+'.lib'})
    }

    $failed=[Collections.Generic.List[string]]::new()
    foreach($id in @('V01','V02','V03','V04','V05','V06')){
        try{
            switch -CaseSensitive ($id){
                'V01' {
                    $expectedKeys='codebook,cohortSnapshot,dependencyProcess,dependencyResult,dependencyReview,dependencySnapshot,descriptor,diagnostic,first,helper,priorCatalog,priorPins,reader,roster,supervisor'
                    $proofCopy=Copy-F2ParentData $ExpectedProofs
                    Assert-F2Parent ((@($proofCopy.Keys|Sort-Object)-join ',') -ceq $expectedKeys)
                    foreach($value in $proofCopy.Values){Assert-F2Parent ($value -is [string] -and $value -cmatch '^[a-f0-9]{64}$')}
                    Assert-F2Parent ($proofCopy.helper -ceq '9972c0eb4d8cf936f252b090a8f0794b0d6b5328a2245b8720cdec32d5fafa53')
                    Assert-F2Parent ($proofCopy.dependencySnapshot -ceq '47b15b415307185f21eb0c06842c26cfc9021f8cb2454830b474b32a203e5391')
                    $dictionaryCopy=Copy-F2ParentData $Dictionary
                    Assert-F2Parent ((@($dictionaryCopy.Keys|Sort-Object)-join ',') -ceq 'contexts,descriptorSha256,kinds,sha256,sites')
                    Assert-F2Parent ($proofCopy.codebook -ceq $dictionaryCopy.sha256 -and $proofCopy.descriptor -ceq $dictionaryCopy.descriptorSha256)
                    Assert-F2Parent ($Dictionary.kinds[3] -ceq 'LibraryInputsSize' -and [Array]::IndexOf([string[]]$Dictionary.sites,'metadata_job_sections') -ge 0 -and [Array]::IndexOf([string[]]$Dictionary.sites,'coff_header_range') -ge 0)
                    Assert-F2ParentValid (New-F2ParentReport)
                    Assert-F2ParentValid (New-F2ParentReport @('missing','missing'))
                    $second=New-F2ParentReport @('missing','selected');Assert-F2ParentValid $second
                    Assert-F2Parent ($second.job.inputCount -eq 1 -and $second.job.attempts -eq 2 -and $second.requests[1].slot -eq 34)
                    # Call the actual fixed authority validator. An unavailable
                    # function or unexpected exception fails V01; never skip it.
                    $liveSummary=New-F2ParentGateSummary
                    $gateResult=Validate-FirstSummary $liveSummary 6 'fixed_two_parent_first_v1'
                    Assert-F2Parent ($null -eq $gateResult)
                    $canonicalSummary=ConvertFrom-Json -InputObject (ConvertTo-F2ParentJson $liveSummary) -Depth 8
                    Assert-F2Parent ($liveSummary -is [Collections.Specialized.OrderedDictionary] -and $canonicalSummary -is [pscustomobject])
                    $gateResult=Validate-FirstSummary $canonicalSummary 6 'fixed_two_parent_first_v1'
                    Assert-F2Parent ($null -eq $gateResult)
                    foreach($key in @('version','kind','executed','passed','failed','failed_case_ids')){
                        $badSummary=New-F2ParentGateSummary;$badSummary.Remove($key)
                        Assert-F2ParentGateSummaryInvalid $badSummary
                    }
                    $badSummary=New-F2ParentGateSummary;$badSummary['extra']=1;Assert-F2ParentGateSummaryInvalid $badSummary
                    foreach($key in @('version','executed','passed','failed')){
                        foreach($type in @('bool','string','double')){
                            $badSummary=New-F2ParentGateSummary
                            switch -CaseSensitive ($type){
                                'bool' {$badSummary[$key]=($key -ne 'failed')}
                                'string' {$badSummary[$key]=[string]$badSummary[$key]}
                                'double' {$badSummary[$key]=[double]$badSummary[$key]}
                            }
                            Assert-F2ParentGateSummaryInvalid $badSummary
                        }
                    }
                    foreach($change in @('version','executed','passed','failed','kind','nonemptyIds','nonarrayIds')){
                        $badSummary=New-F2ParentGateSummary
                        switch -CaseSensitive ($change){
                            'version' {$badSummary.version=2}
                            'executed' {$badSummary.executed=5}
                            'passed' {$badSummary.passed=5}
                            'failed' {$badSummary.failed=1}
                            'kind' {$badSummary.kind='fixed_two_runtime_first_v1'}
                            'nonemptyIds' {$badSummary.failed_case_ids=@('V01')}
                            'nonarrayIds' {$badSummary.failed_case_ids=''}
                        }
                        Assert-F2ParentGateSummaryInvalid $badSummary
                    }
                }
                'V02' {
                    $refused=New-F2ParentReport
                    $site=[Array]::IndexOf([string[]]$Dictionary.sites,'coff_header_range')
                    foreach($request in $refused.requests){
                        $request.candidate.bytes=1;$request.pin.bytes=1
                        $request.strict=@(1,0,$site,$null,$null,$null,0,0,0,$null,$null)
                        $request.profile=@(1,0,$site,$null,$null,$null,0,0,0,$null,$null)
                    }
                    $refused.job.inputBytes=2;$refused.io=[ordered]@{reservedInputs=2;reservedBytes=2;reservedReadBytes=4;actualReadBytes=4}
                    foreach($row in $refused.facts.rows){$row.libraryIds=$null}
                    $refused.facts.bothProfileMetadataAvailable=$false
                    Assert-F2ParentValid $refused
                    Assert-F2Parent $refused.facts.allKnownNamesProvided
                    Assert-F2ParentValid (New-F2ParentGlobalStop)
                    Assert-F2ParentValid (New-F2ParentPrefix)
                    $strictUnknown=New-F2ParentPrefix 'UnknownInspection';$strictUnknown.requests[0].strict=$null;Assert-F2ParentValid $strictUnknown
                    $profileUnknown=New-F2ParentPrefix 'UnknownInspection';$profileUnknown.job.attempts=2;Assert-F2ParentValid $profileUnknown
                    $guardFailure=New-F2ParentStopped 'SearchFailure';$guardFailure.requests[0].outcome='incomplete';Assert-F2ParentValid $guardFailure
                }
                'V03' {
                    foreach($change in @('extra','missing','flagTrue','flagString','proof','boolInteger','stringInteger')){
                        $bad=New-F2ParentReport
                        switch -CaseSensitive ($change){
                            'extra' {$bad['extra']=1}
                            'missing' {$bad.Remove('purpose')}
                            'flagTrue' {$bad.closureComplete=$true}
                            'flagString' {$bad.qualified='false'}
                            'proof' {$bad.proofs.roster='0'*64}
                            'boolInteger' {$bad.job.attempts=$true}
                            'stringInteger' {$bad.job.inputCount='2'}
                        }
                        Assert-F2ParentInvalid $bad
                    }
                    $canonical=(ConvertTo-F2ParentJson (New-F2ParentReport))+[string][char]10
                    Assert-F2Parent ($canonical.Contains('"attempts":4'))
                    Assert-F2ParentRawInvalid ($utf8.GetBytes($canonical.Replace('"attempts":4','"attempts":4.0')))
                    Assert-F2ParentRawInvalid ($utf8.GetBytes(' '+$canonical))
                    Assert-F2ParentRawInvalid ($utf8.GetBytes($canonical+[string][char]10))
                    Assert-F2ParentRawInvalid ([byte[]]@(123,255,125,10))
                }
                'V04' {
                    foreach($change in @('attempts','sections','readBytes','pinSize','profileWithoutStrict','trace')){
                        $bad=New-F2ParentReport
                        switch -CaseSensitive ($change){
                            'attempts' {$bad.job.attempts=3}
                            'sections' {$bad.job.sections=1}
                            'readBytes' {$bad.io.actualReadBytes--}
                            'pinSize' {$bad.requests[0].pin.bytes=21}
                            'profileWithoutStrict' {$bad.requests[0].strict=$null}
                            'trace' {$bad.search.probes[0].index=1}
                        }
                        Assert-F2ParentInvalid $bad
                    }
                    $outside=New-F2ParentPrefix 'InputFailure';Assert-F2ParentInvalid $outside
                    $unknown=New-F2ParentPrefix 'UnknownInspection';$unknown.requests[0].strict=$null;$unknown.job.attempts=2;Assert-F2ParentInvalid $unknown
                    $unknown=New-F2ParentPrefix 'UnknownInspection';Assert-F2ParentInvalid $unknown
                    $zero=New-F2ParentStopped;$zero.job.stopped=$true;Assert-F2ParentInvalid $zero
                    $zero=New-F2ParentStopped;$zero.job.sections=1;Assert-F2ParentInvalid $zero
                    $stop=New-F2ParentGlobalStop;$stop.job.stopped=$false;Assert-F2ParentInvalid $stop
                    $stop=New-F2ParentGlobalStop;$stop.requests[0].strict[2]=[Array]::IndexOf([string[]]$Dictionary.sites,'coff_header_range');Assert-F2ParentInvalid $stop
                    foreach($size in @(0,268435456)){
                        $bad=New-F2ParentStopped 'InputLimit';$bad.search.context=New-F2ParentContext
                        $bad.search.probes=@([ordered]@{index=0;rootIndex=0;outcome='selected'})
                        $bad.requests[0]=New-F2ParentRequest 0 'selected'
                        $bad.requests[0].candidate=[ordered]@{index=0;rootIndex=0;bytes=$size;rootIdentity=$roots[0];leafIdentity='leaf-0'}
                        Assert-F2ParentValid $bad
                        $bad.io=[ordered]@{reservedInputs=1;reservedBytes=$size;reservedReadBytes=2*$size;actualReadBytes=0}
                        Assert-F2ParentInvalid $bad
                    }
                }
                'V05' {
                    $missing=New-F2ParentReport @('missing','missing');Assert-F2ParentValid $missing
                    Assert-F2Parent ($null -eq $missing.facts.providedSlots[4] -and $null -eq $missing.facts.providedSlots[7] -and -not $missing.facts.allKnownNamesProvided)
                    $known=New-F2ParentReport @('selected','selected') @('user32.lib') @();Assert-F2ParentValid $known
                    $index=[Array]::IndexOf([string[]]$known.facts.libraryNames,'user32.lib');Assert-F2Parent ($known.facts.providedSlots[$index] -eq 19)
                    $unknown=New-F2ParentReport @('selected','selected') @('unprovided-new.lib') @();Assert-F2ParentValid $unknown
                    Assert-F2Parent (-not $unknown.facts.allKnownNamesProvided -and $unknown.facts.bothProfileMetadataAvailable)
                    foreach($change in @('priorId','presence','nullEdge','falseJoin','unsafeName','unusedName','typedId')){
                        $bad=New-F2ParentReport
                        switch -CaseSensitive ($change){
                            'priorId' {$bad.facts.priorNameIds[0]=1}
                            'presence' {$bad.facts.providedSlots[4]=$null}
                            'nullEdge' {$bad.facts.rows[0].libraryIds=$null}
                            'falseJoin' {$bad.facts.allKnownNamesProvided=$false}
                            'unsafeName' {$bad.facts.libraryNames[0]='../unsafe.lib'}
                            'unusedName' {$bad.facts.libraryNames+=@('zz-unused.lib');$bad.facts.providedSlots+=@($null);$bad.facts.allKnownNamesProvided=$false}
                            'typedId' {$bad=New-F2ParentReport @('selected','selected') @('kernel32.lib') @();$bad.facts.rows[0].libraryIds[0]='0'}
                        }
                        Assert-F2ParentInvalid $bad
                    }
                    $nullable=New-F2ParentReport @('missing','missing');$nullable.facts.providedSlots[4]=$false;Assert-F2ParentInvalid $nullable
                }
                'V06' {
                    $long=New-F2ParentLongNames 23
                    $max=New-F2ParentReport @('selected','selected') $long @();Assert-F2ParentValid $max
                    Assert-F2Parent ($max.facts.libraryNames.Count -eq 32 -and $long[0].Length -eq 259)
                    $rowNames=@($priorNames)+@($long)
                    $rowMax=New-F2ParentReport @('selected','selected') $rowNames @();Assert-F2ParentValid $rowMax
                    Assert-F2Parent ($rowMax.requests[0].profile[4] -eq 32 -and $rowMax.facts.rows[0].libraryIds.Count -eq 32)
                    Assert-F2ParentInvalid (New-F2ParentReport @('selected','selected') (New-F2ParentLongNames 24) @())
                    Assert-F2ParentInvalid (New-F2ParentReport @('selected','selected') @(('a'*256)+'.lib') @())
                    # Row33 also exceeds union32: this is an overlapping refusal,
                    # not a dynamically isolated reachable resource boundary.
                    $overNames=New-F2ParentLongNames 24;$rowOverNames=@($priorNames)+@($overNames)
                    $rowOver=New-F2ParentReport @('selected','selected') $rowOverNames @()
                    Assert-F2Parent ($rowOver.requests[0].profile[4] -eq 33 -and $rowOver.facts.libraryNames.Count -eq 33)
                    Assert-F2ParentInvalid $rowOver
                    # Oversized raw NUL bytes also violate JSON framing. No extra
                    # field/padding capability or valid oversized report is claimed.
                    Assert-F2ParentRawInvalid ([byte[]]::new(24577))
                    foreach($value in @($max,$rowMax)){
                        $outer=Copy-F2ParentData $value;$outer.facts=$null
                        Assert-F2Parent ($utf8.GetByteCount((ConvertTo-F2ParentJson $outer)+[string][char]10) -le 12288)
                        Assert-F2Parent ($utf8.GetByteCount((ConvertTo-F2ParentJson $value.facts)+[string][char]10) -le 12288)
                    }
                }
            }
        }catch{$failed.Add($id)}
    }
    return [ordered]@{version=1;kind='fixed_two_parent_first_v1';executed=6;passed=6-$failed.Count;failed=$failed.Count;failed_case_ids=$failed.ToArray()}
}
