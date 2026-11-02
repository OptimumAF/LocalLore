# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
# Independent SOURCE-ONLY / UNRUN parent FIRST. Pure synthetic JSON/byte data.
# No top-level execution, files, environment, SDK, process, network or source evaluation.
# ExpectedProofs and ExpectedPin are trusted PSCustomObject/JSON-data values.
# The production validator receives the authenticated pin separately. Fixtures
# retain its public fixed fields but replace BOTH identities with synthetic tokens.
function Assert-PaddingFirst($Condition) {
    if(-not $Condition){throw 'PaddingParentFirstAssertion'}
}
function Copy-PaddingFirstData($Value) {
    return ConvertFrom-Json -InputObject (ConvertTo-Json -InputObject $Value -Depth 20 -Compress -ErrorAction Stop) -Depth 20 -ErrorAction Stop
}
function Get-PaddingFirstWire($Value) {
    $text=(ConvertTo-Json -InputObject $Value -Depth 20 -Compress -ErrorAction Stop)+[string][char]10
    return ,([Text.UTF8Encoding]::new($false).GetBytes($text))
}
function New-PaddingFirstSummary([int]$Passed,[string[]]$Failed=@()) {
    return [ordered]@{version=1;kind='ucrt_padding_parent_first_v1';executed=6;passed=$Passed;failed=$Failed.Count;failed_case_ids=$Failed}
}
function New-PaddingFirstPin($ExpectedPin) {
    $pin=Copy-PaddingFirstData $ExpectedPin
    $pin.rootIdentity='padding-root';$pin.leafIdentity='padding-leaf'
    return $pin
}
function New-PaddingFirstHeader([int]$Index,[long]$Offset,[long]$Bytes,[int]$Pad=10) {
    $start=$Offset+60;$end=$start+$Bytes;$odd=($Bytes%2 -eq 1)
    return [pscustomobject][ordered]@{index=$Index;offset=$Offset;bytes=$Bytes;bodyStart=$start;bodyEnd=$end
        paddingRequired=$odd;paddingOffset=$(if($odd){$end}else{$null});paddingByte=$(if($odd){$Pad}else{$null})}
}
function Convert-PaddingFirstAsciiHex([string]$Value) {
    return [Convert]::ToHexString([Text.Encoding]::ASCII.GetBytes($Value)).ToLowerInvariant()
}
function New-PaddingFirstReport($ExpectedProofs,$ExpectedPin,[int]$Pad=0,[bool]$Even=$false) {
    $pin=New-PaddingFirstPin $ExpectedPin
    $headers=@(
        (New-PaddingFirstHeader 0 8 1)
        (New-PaddingFirstHeader 1 70 2)
        (New-PaddingFirstHeader 2 132 0)
        (New-PaddingFirstHeader 3 192 98199)
        (New-PaddingFirstHeader 4 98452 $(if($Even){2}else{3}) $Pad)
    )
    $last=$headers[4]
    $sizeText=([string]$last.bytes).PadRight(10,' ')
    $target=[pscustomobject][ordered]@{memberIndex=4;memberOffset=98452;memberBytes=$last.bytes
        bodyStart=$last.bodyStart;bodyEnd=$last.bodyEnd;paddingRequired=$last.paddingRequired
        paddingOffset=$last.paddingOffset;paddingByte=$last.paddingByte
        nameHex=(Convert-PaddingFirstAsciiHex ('member4/'.PadRight(16,' ')))
        sizeHex=(Convert-PaddingFirstAsciiHex $sizeText);endHex='600a'}
    return [pscustomobject][ordered]@{
        version=1;kind='ucrt_padding_observation_v1';purpose='build_input_error_site_only'
        qualified=$false;linkQualification=$false;closureComplete=$false;captureComplete=$true;status='complete'
        selfchecks=[pscustomobject][ordered]@{version=1;kind='ucrt_padding_first_v1';executed=24;passed=24;failed=0;failed_case_ids=@()}
        proofs=(Copy-PaddingFirstData $ExpectedProofs);input=$pin
        io=[pscustomobject][ordered]@{reservedInputs=1;reservedBytes=285588;reservedReadBytes=571176
            actualReadBytes=571176;opened=$true;closed=$true;verifiedPasses=2}
        observation=[pscustomobject][ordered]@{headers=$headers;target=$target}
        priorRefusal=[pscustomobject][ordered]@{kind='LibraryInputsFormat';site='archive_padding_byte';memberIndex=4;memberOffset=98452}
        matchesPriorRefusal=($last.paddingRequired -and $last.paddingByte -ne 10);critical=$null
    }
}
function New-PaddingFirstIo([int]$Reserved=0,[long]$Actual=0,[bool]$Opened=$false,[bool]$Closed=$false,[int]$Passes=0) {
    return [pscustomobject][ordered]@{reservedInputs=$Reserved
        reservedBytes=$(if($Reserved -eq 1){285588}else{0})
        reservedReadBytes=$(if($Reserved -eq 1){571176}else{0})
        actualReadBytes=$Actual;opened=$Opened;closed=$Closed;verifiedPasses=$Passes}
}
function New-PaddingFirstStopped($ExpectedProofs,$ExpectedPin,[string]$Critical,$Io) {
    $report=New-PaddingFirstReport $ExpectedProofs $ExpectedPin
    $report.captureComplete=$false;$report.status='stopped';$report.observation=$null
    $report.matchesPriorRefusal=$null;$report.critical=$Critical;$report.io=$Io
    return $report
}
function Assert-PaddingFirstAccepted($Report,$ExpectedProofs,$ExpectedPin) {
    [byte[]]$wire=Get-PaddingFirstWire $Report
    $pin=New-PaddingFirstPin $ExpectedPin
    $actual=Validate-PaddingReport $wire $ExpectedProofs $pin
    [byte[]]$roundtrip=Get-PaddingFirstWire $actual
    Assert-PaddingFirst ([Convert]::ToBase64String($wire) -ceq [Convert]::ToBase64String($roundtrip))
    Assert-PaddingFirst ($wire.Length -le 8192)
}
function Assert-PaddingFirstRawRejected([byte[]]$Wire,$ExpectedProofs,$ExpectedPin) {
    $caught=$null
    try{$null=Validate-PaddingReport $Wire $ExpectedProofs (New-PaddingFirstPin $ExpectedPin)}
    catch{$caught=$_.Exception.Message}
    Assert-PaddingFirst ($caught -ceq 'InvalidPaddingObservationReport')
}
function Assert-PaddingFirstRejected($Report,$ExpectedProofs,$ExpectedPin) {
    Assert-PaddingFirstRawRejected (Get-PaddingFirstWire $Report) $ExpectedProofs $ExpectedPin
}
function Assert-PaddingFirstSummaryRejected($Value) {
    $caught=$null
    try{$null=Validate-PaddingParentSummary $Value}catch{$caught=$_.Exception.Message}
    Assert-PaddingFirst ($caught -ceq 'InvalidPaddingParentSummary')
}
function Invoke-PaddingParentSelfchecksV1($ExpectedProofs,$ExpectedPin) {
    $cases=[Collections.Generic.List[object]]::new()
    $cases.Add(@('V01',{
        # Use the SAME OrderedDictionary constructor as the actual return below.
        $live=New-PaddingFirstSummary -Passed 6 -Failed @()
        Assert-PaddingFirst ($live -is [Collections.Specialized.OrderedDictionary])
        $liveResult=Validate-PaddingParentSummary $live
        Assert-PaddingFirst ($null -eq $liveResult)
        [byte[]]$wire=Get-PaddingFirstWire $live
        $canonical=ConvertFrom-Json -InputObject ([Text.Encoding]::UTF8.GetString($wire)) -Depth 8 -ErrorAction Stop
        $canonicalResult=Validate-PaddingParentSummary $canonical
        Assert-PaddingFirst ($null -eq $canonicalResult)
        Assert-PaddingFirst ($canonical.kind -ceq 'ucrt_padding_parent_first_v1' -and $canonical.executed -eq 6)
        foreach($mutate in @(
            {$args[0].version=2},{$args[0].kind='ucrt_padding_first_v1'},
            {$args[0].executed=5},{$args[0].passed=5},{$args[0].failed=1},
            {$args[0].failed_case_ids=@('V01')},{$args[0].executed=$true},
            {$args[0].executed='6'},{$args[0].executed=[double]6.0},
            {$args[0]|Add-Member -NotePropertyName extra -NotePropertyValue 1},
            {$args[0].PSObject.Properties.Remove('kind')}
        )){
            $bad=Copy-PaddingFirstData $live;& $mutate $bad
            Assert-PaddingFirstSummaryRejected $bad
        }
        Assert-PaddingFirstSummaryRejected $null
        Assert-PaddingFirstSummaryRejected @($canonical)
        Assert-PaddingFirstSummaryRejected @{version=1;kind='ucrt_padding_parent_first_v1';executed=6;passed=6;failed=0;failed_case_ids=@()}
        $failed=New-PaddingFirstSummary -Passed 5 -Failed @('V01')
        Assert-PaddingFirstSummaryRejected $failed
    }))
    $cases.Add(@('V02',{
        foreach($variant in @(@(0,$false,$true),@(10,$false,$false),@(255,$false,$true),@(0,$true,$false))){
            $report=New-PaddingFirstReport $ExpectedProofs $ExpectedPin $variant[0] $variant[1]
            Assert-PaddingFirst ($report.matchesPriorRefusal -ceq $variant[2])
            Assert-PaddingFirst ($report.observation.headers.Count -eq 5 -and
                $report.observation.target.memberIndex -eq 4 -and $report.observation.target.memberOffset -eq 98452)
            Assert-PaddingFirstAccepted $report $ExpectedProofs $ExpectedPin
        }
        $report=New-PaddingFirstReport $ExpectedProofs $ExpectedPin
        Assert-PaddingFirst ($report.input.name -ceq 'ucrt.lib' -and $report.input.rootIndex -eq 3 -and
            $report.input.sourceSlot -eq 33 -and $report.input.bytes -eq 285588 -and
            $report.input.expectedSha256 -ceq '7ef4eac926bf597d2f243f16cdfed7e0db22cb3ca34a1d7e088a84c994a03d66')
        # Leading zeroes are valid accepted decimal syntax, not a new restriction.
        $report.observation.target.sizeHex=Convert-PaddingFirstAsciiHex '0000000003'
        Assert-PaddingFirstAccepted $report $ExpectedProofs $ExpectedPin
    }))
    $cases.Add(@('V03',{
        foreach($mutate in @(
            {$args[0].qualified=$true},{$args[0].linkQualification=$true},{$args[0].closureComplete=$true},
            {$args[0].version=2},{$args[0].kind='other'},{$args[0].purpose='other'},
            {$args[0].captureComplete=$false},{$args[0].status='stopped'},{$args[0].critical='PaddingRead'},
            {$args[0]|Add-Member -NotePropertyName extra -NotePropertyValue 1},
            {$args[0].PSObject.Properties.Remove('critical')},
            {$args[0].observation|Add-Member -NotePropertyName extra -NotePropertyValue 1},
            {$args[0].input.name='other.lib'},{$args[0].input.rootIndex=2},{$args[0].input.sourceSlot=34},
            {$args[0].input.bytes=285587},{$args[0].input.expectedSha256='0'*64},
            {$args[0].input.rootIdentity='other-root'},{$args[0].input.leafIdentity='other-leaf'},
            {$args[0].input|Add-Member -NotePropertyName path -NotePropertyValue 'forbidden'},
            {$args[0].input.PSObject.Properties.Remove('leafIdentity')},
            {$args[0].selfchecks.executed=23},{$args[0].selfchecks.kind='ucrt_padding_parent_first_v1'},
            {$args[0].selfchecks.passed=23;$args[0].selfchecks.failed=1;$args[0].selfchecks.failed_case_ids=@('E01')},
            {$args[0].priorRefusal.kind='LibraryInputsSize'},{$args[0].priorRefusal.site='archive_member_range'},
            {$args[0].priorRefusal.memberIndex=3},{$args[0].priorRefusal.memberOffset=98450},
            {$args[0].matchesPriorRefusal=$false}
        )){
            $bad=New-PaddingFirstReport $ExpectedProofs $ExpectedPin;& $mutate $bad
            Assert-PaddingFirstRejected $bad $ExpectedProofs $ExpectedPin
        }
        foreach($key in @('module','first','parentFirst','reader','supervisor','roster',
            'predecessorSnapshot','predecessorProcess','predecessorResult','predecessorRootReview','descriptor')){
            $bad=New-PaddingFirstReport $ExpectedProofs $ExpectedPin
            $bad.proofs.$key=$(if($bad.proofs.$key -ceq ('a'*64)){'b'*64}else{'a'*64})
            Assert-PaddingFirstRejected $bad $ExpectedProofs $ExpectedPin
        }
        foreach($change in @('extra','missing','uppercase')){
            $bad=New-PaddingFirstReport $ExpectedProofs $ExpectedPin
            if($change -ceq 'extra'){$bad.proofs|Add-Member -NotePropertyName extra -NotePropertyValue ('a'*64)}
            elseif($change -ceq 'missing'){$bad.proofs.PSObject.Properties.Remove('module')}
            else{$bad.proofs.module='A'*64}
            Assert-PaddingFirstRejected $bad $ExpectedProofs $ExpectedPin
        }
        # Fixed production input constraints apply even if both supplied pins agree.
        $pin=New-PaddingFirstPin $ExpectedPin;$pin.rootIndex=2
        $bad=New-PaddingFirstReport $ExpectedProofs $ExpectedPin;$bad.input=Copy-PaddingFirstData $pin
        $caught=$null;try{$null=Validate-PaddingReport (Get-PaddingFirstWire $bad) $ExpectedProofs $pin}catch{$caught=$_.Exception.Message}
        Assert-PaddingFirst ($caught -ceq 'InvalidPaddingObservationReport')
        foreach($mutate in @({$args[0].rootIdentity='a'*257},{$args[0].leafIdentity=[string][char]233},{$args[0].expectedSha256='G'*64})){
            $pin=New-PaddingFirstPin $ExpectedPin;& $mutate $pin
            $bad=New-PaddingFirstReport $ExpectedProofs $ExpectedPin;$bad.input=Copy-PaddingFirstData $pin
            $caught=$null;try{$null=Validate-PaddingReport (Get-PaddingFirstWire $bad) $ExpectedProofs $pin}catch{$caught=$_.Exception.Message}
            Assert-PaddingFirst ($caught -ceq 'InvalidPaddingObservationReport')
        }
    }))
    $cases.Add(@('V04',{
        $report=New-PaddingFirstReport $ExpectedProofs $ExpectedPin
        [byte[]]$wire=Get-PaddingFirstWire $report
        $text=[Text.Encoding]::UTF8.GetString($wire);$body=$text.Substring(0,$text.Length-1)
        foreach($badText in @($body,($text+[char]10),(' '+$text),($body+' '+[char]10),($body+[char]13+[char]10),
            $text.Replace('"version":1,','"version":1,"version":1,'))){
            Assert-PaddingFirstRawRejected ([Text.Encoding]::UTF8.GetBytes($badText)) $ExpectedProofs $ExpectedPin
        }
        Assert-PaddingFirstRawRejected $null $ExpectedProofs $ExpectedPin
        Assert-PaddingFirstRawRejected ([byte[]]@()) $ExpectedProofs $ExpectedPin
        Assert-PaddingFirstRawRejected ([byte[]](239,187,191)+$wire) $ExpectedProofs $ExpectedPin
        Assert-PaddingFirstRawRejected ([byte[]](255,10)) $ExpectedProofs $ExpectedPin
        # Oversize is also malformed data; no isolated valid-schema 8193B claim.
        $large=[byte[]]::new(8193);$large[8192]=10
        Assert-PaddingFirstRawRejected $large $ExpectedProofs $ExpectedPin
        foreach($mutate in @(
            {$args[0].version=$true},{$args[0].input.rootIndex='3'},{$args[0].input.rootIndex=[double]3.5},
            {$args[0].input.bytes=-1},{$args[0].input.bytes=9007199254740992L},
            {$args[0].observation.headers[0].index=$false},
            {$args[0].observation.headers[0].bytes=[double]1.5},
            {$args[0].matchesPriorRefusal=1},{$args[0].io.opened=1},{$args[0].io.closed=1},
            {$args[0].qualified=0},{$args[0].linkQualification='false'},{$args[0].closureComplete=$null},
            {$args[0].captureComplete=1},{$args[0].observation.headers[0].paddingRequired=1},
            {$args[0].io.reservedInputs=$true},{$args[0].io.verifiedPasses='2'},
            {$args[0].selfchecks.failed_case_ids=@($null)}
        )){
            $bad=New-PaddingFirstReport $ExpectedProofs $ExpectedPin;& $mutate $bad
            Assert-PaddingFirstRejected $bad $ExpectedProofs $ExpectedPin
        }
    }))
    $cases.Add(@('V05',{
        foreach($mutate in @(
            {$args[0].observation.headers=@($args[0].observation.headers[0..3])},
            {$args[0].observation.headers+=Copy-PaddingFirstData $args[0].observation.headers[4]},
            {$args[0].observation.headers[0].offset=10},
            {$args[0].observation.headers[1].index=0},
            {$args[0].observation.headers[1].offset=71},
            {$args[0].observation.headers[2].bodyStart=193},
            {$args[0].observation.headers[3].bodyEnd=98450},
            {$args[0].observation.headers[3].paddingRequired=$false},
            {$args[0].observation.headers[3].paddingOffset=98450},
            {$args[0].observation.headers[3].paddingByte=0},
            {$args[0].observation.headers[0].paddingByte=$null},
            {$args[0].observation.headers[1].paddingOffset=132},
            {$args[0].observation.headers[1].paddingByte=10},
            {$args[0].observation.headers[4].bytes=2},
            {$args[0].observation.target.memberIndex=3},{$args[0].observation.target.memberOffset=98450},
            {$args[0].observation.target.memberBytes=2},{$args[0].observation.target.bodyStart=98513},
            {$args[0].observation.target.paddingRequired=$false},
            {$args[0].observation.target.paddingOffset=$null},
            {$args[0].observation.target.paddingByte=1},
            {$args[0].observation.target.nameHex=$args[0].observation.target.nameHex.ToUpperInvariant()},
            {$args[0].observation.target.nameHex='00'+('20'*15)},
            {$args[0].observation.target.nameHex='gg'*16},
            {$args[0].observation.target.sizeHex=Convert-PaddingFirstAsciiHex '+3        '},
            {$args[0].observation.target.sizeHex=Convert-PaddingFirstAsciiHex ' 3        '},
            {$args[0].observation.target.sizeHex=Convert-PaddingFirstAsciiHex '3x        '},
            {$args[0].observation.target.sizeHex=Convert-PaddingFirstAsciiHex '2         '},
            {$args[0].observation.target.endHex='600b'},
            {$args[0].observation.target|Add-Member -NotePropertyName extra -NotePropertyValue 1}
        )){
            $bad=New-PaddingFirstReport $ExpectedProofs $ExpectedPin;& $mutate $bad
            Assert-PaddingFirstRejected $bad $ExpectedProofs $ExpectedPin
        }
        $bad=New-PaddingFirstReport $ExpectedProofs $ExpectedPin
        $bad.observation.headers[4].bytes=200000;$bad.observation.headers[4].bodyEnd=298512
        $bad.observation.headers[4].paddingRequired=$false;$bad.observation.headers[4].paddingOffset=$null;$bad.observation.headers[4].paddingByte=$null
        $bad.observation.target.memberBytes=200000;$bad.observation.target.bodyEnd=298512
        $bad.observation.target.paddingRequired=$false;$bad.observation.target.paddingOffset=$null;$bad.observation.target.paddingByte=$null
        $bad.observation.target.sizeHex=Convert-PaddingFirstAsciiHex '200000    ';$bad.matchesPriorRefusal=$false
        Assert-PaddingFirstRejected $bad $ExpectedProofs $ExpectedPin
    }))
    $cases.Add(@('V06',{
        foreach($code in @('PaddingPin','PaddingType','PaddingStopped','PaddingSource')){
            Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin $code (New-PaddingFirstIo)) $ExpectedProofs $ExpectedPin
        }
        foreach($code in @('PaddingSignature','PaddingHeader','PaddingSize','PaddingBounds','PaddingPrefix','PaddingTarget','PaddingType')){
            Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin $code (New-PaddingFirstIo 1 571176 $true $true 2)) $ExpectedProofs $ExpectedPin
        }
        foreach($code in @('PaddingIdentity','PaddingRead','PaddingStopped','PaddingSource')){
            Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin $code (New-PaddingFirstIo 1)) $ExpectedProofs $ExpectedPin
        }
        # Malformed acquired wrapper/no cleanup and first-cause + close failure
        # remain truthful opened=true/closed=false. They are not sole Close errors.
        foreach($code in @('PaddingIdentity','PaddingRead','PaddingStopped')){
            Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin $code (New-PaddingFirstIo 1 0 $true $false 0)) $ExpectedProofs $ExpectedPin
        }
        Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingIdentity' (New-PaddingFirstIo 1 285588 $true $false 1)) $ExpectedProofs $ExpectedPin
        Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingIdentity' (New-PaddingFirstIo 1 571176 $true $false 2)) $ExpectedProofs $ExpectedPin
        Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingRead' (New-PaddingFirstIo 1 285588 $true $false 1)) $ExpectedProofs $ExpectedPin
        Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingSource' (New-PaddingFirstIo 1 571176 $true $true 2)) $ExpectedProofs $ExpectedPin
        Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingRead' (New-PaddingFirstIo 1 17 $true $false 0)) $ExpectedProofs $ExpectedPin
        Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingStopped' (New-PaddingFirstIo 1 11 $true $true 0)) $ExpectedProofs $ExpectedPin
        foreach($closed in @($true,$false)){
            Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingHash' (New-PaddingFirstIo 1 285588 $true $closed 0)) $ExpectedProofs $ExpectedPin
        }
        Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingHash' (New-PaddingFirstIo 1 571176 $true $true 2)) $ExpectedProofs $ExpectedPin
        Assert-PaddingFirstAccepted (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingClose' (New-PaddingFirstIo 1 571176 $true $false 2)) $ExpectedProofs $ExpectedPin
        foreach($mutate in @(
            {$args[0].io.reservedInputs=2},{$args[0].io.reservedBytes=1},{$args[0].io.reservedReadBytes=1},
            {$args[0].io.actualReadBytes=571177},{$args[0].io.actualReadBytes=-1},
            {$args[0].io.actualReadBytes=[double]1.5},{$args[0].io.verifiedPasses=3},
            {$args[0].io.verifiedPasses=1;$args[0].io.actualReadBytes=285587},
            {$args[0].io.verifiedPasses=2;$args[0].io.actualReadBytes=571175},
            {$args[0].io.opened=$false},{$args[0].io.closed=$false},
            {$args[0].io|Add-Member -NotePropertyName extra -NotePropertyValue 1},
            {$args[0].io.PSObject.Properties.Remove('verifiedPasses')}
        )){
            $bad=New-PaddingFirstReport $ExpectedProofs $ExpectedPin;& $mutate $bad
            Assert-PaddingFirstRejected $bad $ExpectedProofs $ExpectedPin
        }
        foreach($mutate in @(
            {$args[0].io.reservedBytes=1},{$args[0].io.reservedReadBytes=1},
            {$args[0].io.actualReadBytes=1},{$args[0].io.verifiedPasses=1},
            {$args[0].io.opened=$true},{$args[0].io.closed=$true}
        )){
            $bad=New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingSource' (New-PaddingFirstIo)
            & $mutate $bad;Assert-PaddingFirstRejected $bad $ExpectedProofs $ExpectedPin
        }
        foreach($code in @('PaddingIdentity','PaddingRead')){
            Assert-PaddingFirstRejected (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin $code (New-PaddingFirstIo)) $ExpectedProofs $ExpectedPin
        }
        Assert-PaddingFirstRejected (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingPin' (New-PaddingFirstIo 1)) $ExpectedProofs $ExpectedPin
        Assert-PaddingFirstRejected (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingType' (New-PaddingFirstIo 1)) $ExpectedProofs $ExpectedPin
        Assert-PaddingFirstRejected (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingHash' (New-PaddingFirstIo 1 285587 $true $true 0)) $ExpectedProofs $ExpectedPin
        foreach($io in @((New-PaddingFirstIo 1 571176 $true $true 2),(New-PaddingFirstIo 1 571176 $true $false 1))){
            Assert-PaddingFirstRejected (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingClose' $io) $ExpectedProofs $ExpectedPin
        }
        foreach($code in @('PaddingSignature','PaddingHeader','PaddingSize','PaddingBounds','PaddingPrefix','PaddingTarget')){
            Assert-PaddingFirstRejected (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin $code (New-PaddingFirstIo 1 17 $true $true 0)) $ExpectedProofs $ExpectedPin
        }
        foreach($code in @('PaddingReport','UnexpectedCause')){
            Assert-PaddingFirstRejected (New-PaddingFirstStopped $ExpectedProofs $ExpectedPin $code (New-PaddingFirstIo)) $ExpectedProofs $ExpectedPin
        }
        $bad=New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingSource' (New-PaddingFirstIo)
        $bad.matchesPriorRefusal=$false;Assert-PaddingFirstRejected $bad $ExpectedProofs $ExpectedPin
        $bad=New-PaddingFirstStopped $ExpectedProofs $ExpectedPin 'PaddingSource' (New-PaddingFirstIo)
        $bad.observation=(New-PaddingFirstReport $ExpectedProofs $ExpectedPin).observation
        Assert-PaddingFirstRejected $bad $ExpectedProofs $ExpectedPin
    }))
    [string[]]$expected=@('V01','V02','V03','V04','V05','V06')
    Assert-PaddingFirst ($cases.Count -eq 6)
    $failed=[Collections.Generic.List[string]]::new()
    for($i=0;$i -lt 6;$i++){
        Assert-PaddingFirst ($cases[$i][0] -ceq $expected[$i])
        $run=$cases[$i][1]
        try{& $run}catch{$failed.Add($expected[$i])}
    }
    return New-PaddingFirstSummary -Passed (6-$failed.Count) -Failed $failed.ToArray()
}
