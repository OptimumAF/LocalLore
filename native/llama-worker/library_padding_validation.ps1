# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
# Pure padding-report validation. No top-level work, I/O or source execution.
# Trusted expected-proof/pin arguments are PSCustomObject/JSON data.
function Assert-PaddingValidation($Condition) {
    if(-not $Condition){throw 'PaddingValidation'}
}
function Test-PaddingValidationUInt($Value,[long]$Maximum=9007199254740991) {
    return (($Value -is [byte] -or $Value -is [sbyte] -or $Value -is [int16] -or
        $Value -is [uint16] -or $Value -is [int32] -or $Value -is [uint32] -or
        $Value -is [int64] -or $Value -is [uint64]) -and $Value -ge 0 -and $Value -le $Maximum)
}
function Test-PaddingValidationFields($Value,[string[]]$Names) {
    if($null -eq $Value -or $Value -isnot [pscustomobject]){return $false}
    $properties=@($Value.PSObject.Properties)
    if($properties.Count -ne $Names.Count){return $false}
    foreach($property in $properties){
        if($property.MemberType -ne [Management.Automation.PSMemberTypes]::NoteProperty){return $false}
    }
    [string[]]$actual=@($properties.Name);[string[]]$expected=@($Names)
    [Array]::Sort($actual,[StringComparer]::Ordinal)
    [Array]::Sort($expected,[StringComparer]::Ordinal)
    return (($actual -join ',') -ceq ($expected -join ','))
}
function Test-PaddingValidationString($Value,[string]$Expected) {
    return ($Value -is [string] -and $Value -ceq $Expected)
}
function Test-PaddingValidationHex($Value) {
    return ($Value -is [string] -and $Value -cmatch '\A[a-f0-9]{64}\z')
}
function Test-PaddingValidationIdentity($Value) {
    return ($Value -is [string] -and $Value -cmatch '\A[A-Za-z0-9_.:-]{1,256}\z')
}
function Assert-PaddingValidationSummary($Value,[string]$Kind,[int]$Count) {
    Assert-PaddingValidation (Test-PaddingValidationFields $Value @('version','kind','executed','passed','failed','failed_case_ids'))
    Assert-PaddingValidation ((Test-PaddingValidationUInt $Value.version 1) -and $Value.version -eq 1 -and
        (Test-PaddingValidationString $Value.kind $Kind) -and
        (Test-PaddingValidationUInt $Value.executed $Count) -and $Value.executed -eq $Count -and
        (Test-PaddingValidationUInt $Value.passed $Count) -and $Value.passed -eq $Count -and
        (Test-PaddingValidationUInt $Value.failed 0) -and
        $Value.failed_case_ids -is [array] -and $Value.failed_case_ids.Count -eq 0)
}
function Validate-PaddingParentSummary($Value) {
    try{
        # This exception applies ONLY to the trusted suite-return handoff.
        if($Value -is [Collections.Specialized.OrderedDictionary]){$Value=[pscustomobject]$Value}
        Assert-PaddingValidationSummary $Value 'ucrt_padding_parent_first_v1' 6
        return
    }catch{throw 'InvalidPaddingParentSummary'}
}
function Assert-PaddingValidationPin($Value) {
    Assert-PaddingValidation (Test-PaddingValidationFields $Value @('name','rootIndex','sourceSlot','bytes','expectedSha256','rootIdentity','leafIdentity'))
    Assert-PaddingValidation ((Test-PaddingValidationString $Value.name 'ucrt.lib') -and
        (Test-PaddingValidationUInt $Value.rootIndex 3) -and $Value.rootIndex -eq 3 -and
        (Test-PaddingValidationUInt $Value.sourceSlot 33) -and $Value.sourceSlot -eq 33 -and
        (Test-PaddingValidationUInt $Value.bytes 285588) -and $Value.bytes -eq 285588 -and
        (Test-PaddingValidationHex $Value.expectedSha256) -and
        $Value.expectedSha256 -ceq '7ef4eac926bf597d2f243f16cdfed7e0db22cb3ca34a1d7e088a84c994a03d66' -and
        (Test-PaddingValidationIdentity $Value.rootIdentity) -and
        (Test-PaddingValidationIdentity $Value.leafIdentity))
}
function Test-PaddingValidationIo($Io) {
    Assert-PaddingValidation (Test-PaddingValidationFields $Io @('reservedInputs','reservedBytes','reservedReadBytes','actualReadBytes','opened','closed','verifiedPasses'))
    Assert-PaddingValidation ((Test-PaddingValidationUInt $Io.reservedInputs 1) -and
        (Test-PaddingValidationUInt $Io.reservedBytes 285588) -and
        (Test-PaddingValidationUInt $Io.reservedReadBytes 571176) -and
        (Test-PaddingValidationUInt $Io.actualReadBytes $Io.reservedReadBytes) -and
        (Test-PaddingValidationUInt $Io.verifiedPasses 2) -and
        $Io.opened -is [bool] -and $Io.closed -is [bool])
    if($Io.reservedInputs -eq 0){
        Assert-PaddingValidation ($Io.reservedBytes -eq 0 -and $Io.reservedReadBytes -eq 0 -and
            $Io.actualReadBytes -eq 0 -and $Io.verifiedPasses -eq 0 -and -not $Io.opened -and -not $Io.closed)
    }else{
        Assert-PaddingValidation ($Io.reservedBytes -eq 285588 -and $Io.reservedReadBytes -eq 571176)
    }
    Assert-PaddingValidation (-not $Io.closed -or $Io.opened)
    if(-not $Io.opened){
        Assert-PaddingValidation ($Io.actualReadBytes -eq 0 -and $Io.verifiedPasses -eq 0 -and -not $Io.closed)
    }
    Assert-PaddingValidation ($Io.actualReadBytes -ge 285588*$Io.verifiedPasses)
    return ($Io.reservedInputs -eq 1 -and $Io.actualReadBytes -eq 571176 -and
        $Io.opened -and $Io.closed -and $Io.verifiedPasses -eq 2)
}
function Convert-PaddingValidationAsciiHex($Value,[int]$Bytes) {
    Assert-PaddingValidation ($Value -is [string] -and $Value.Length -eq 2*$Bytes -and
        $Value -cmatch '\A[a-f0-9]+\z')
    $decoded=[Convert]::FromHexString($Value)
    foreach($byte in $decoded){Assert-PaddingValidation ($byte -ge 32 -and $byte -le 126)}
    return [Text.Encoding]::ASCII.GetString($decoded)
}
function Assert-PaddingValidationObservation($Observation) {
    Assert-PaddingValidation (Test-PaddingValidationFields $Observation @('headers','target'))
    Assert-PaddingValidation ($Observation.headers -is [array] -and $Observation.headers.Count -eq 5)
    [long]$next=8
    for($index=0;$index -lt 5;$index++){
        $header=$Observation.headers[$index]
        Assert-PaddingValidation (Test-PaddingValidationFields $header @('index','offset','bytes','bodyStart','bodyEnd','paddingRequired','paddingOffset','paddingByte'))
        foreach($field in @('index','offset','bytes','bodyStart','bodyEnd')){
            Assert-PaddingValidation (Test-PaddingValidationUInt $header.$field 285588)
        }
        Assert-PaddingValidation ($header.index -eq $index -and $header.offset -eq $next -and
            $header.offset -ge 8 -and $header.offset%2 -eq 0 -and
            $header.bodyStart -eq $header.offset+60 -and $header.bodyEnd -eq $header.bodyStart+$header.bytes -and
            $header.paddingRequired -is [bool] -and $header.paddingRequired -eq ($header.bytes%2 -eq 1))
        if($header.paddingRequired){
            Assert-PaddingValidation ((Test-PaddingValidationUInt $header.paddingOffset 285587) -and
                $header.paddingOffset -eq $header.bodyEnd -and (Test-PaddingValidationUInt $header.paddingByte 255))
            if($index -lt 4){Assert-PaddingValidation ($header.paddingByte -eq 10)}
            $next=$header.bodyEnd+1
        }else{
            Assert-PaddingValidation ($null -eq $header.paddingOffset -and $null -eq $header.paddingByte)
            $next=$header.bodyEnd
        }
    }
    $target=$Observation.target;$last=$Observation.headers[4]
    Assert-PaddingValidation (Test-PaddingValidationFields $target @('memberIndex','memberOffset','memberBytes','bodyStart','bodyEnd','paddingRequired','paddingOffset','paddingByte','nameHex','sizeHex','endHex'))
    foreach($field in @('memberIndex','memberOffset','memberBytes','bodyStart','bodyEnd')){
        Assert-PaddingValidation (Test-PaddingValidationUInt $target.$field 285588)
    }
    Assert-PaddingValidation ($target.memberIndex -eq 4 -and $target.memberOffset -eq 98452 -and
        $target.memberIndex -eq $last.index -and $target.memberOffset -eq $last.offset -and
        $target.memberBytes -eq $last.bytes -and $target.bodyStart -eq $last.bodyStart -and $target.bodyEnd -eq $last.bodyEnd -and
        $target.paddingRequired -is [bool] -and $target.paddingRequired -eq $last.paddingRequired)
    if($last.paddingRequired){
        Assert-PaddingValidation ((Test-PaddingValidationUInt $target.paddingOffset 285587) -and
            (Test-PaddingValidationUInt $target.paddingByte 255) -and
            $target.paddingOffset -eq $last.paddingOffset -and $target.paddingByte -eq $last.paddingByte)
    }else{
        Assert-PaddingValidation ($null -eq $target.paddingOffset -and $null -eq $target.paddingByte)
    }
    $null=Convert-PaddingValidationAsciiHex $target.nameHex 16
    $size=Convert-PaddingValidationAsciiHex $target.sizeHex 10
    $digits=$size.TrimEnd([char[]]@([char]32))
    Assert-PaddingValidation ($digits -cmatch '^[0-9]+$')
    $number=[long]::Parse($digits,[Globalization.NumberStyles]::None,[Globalization.CultureInfo]::InvariantCulture)
    Assert-PaddingValidation ($number -eq $target.memberBytes -and (Test-PaddingValidationString $target.endHex '600a'))
}
function Validate-PaddingReport([byte[]]$Raw,$ExpectedProofs,$ExpectedPin) {
    try{
        Assert-PaddingValidation ($null -ne $Raw -and $Raw.Length -gt 0 -and $Raw.Length -le 8192)
        $utf8=[Text.UTF8Encoding]::new($false,$true)
        $wire=$utf8.GetString($Raw)
        Assert-PaddingValidation ($wire.EndsWith([string][char]10,[StringComparison]::Ordinal))
        $report=ConvertFrom-Json -InputObject $wire -Depth 16 -ErrorAction Stop
        Assert-PaddingValidation (Test-PaddingValidationFields $report @('version','kind','purpose','qualified','linkQualification','closureComplete','captureComplete','status','selfchecks','proofs','input','io','observation','priorRefusal','matchesPriorRefusal','critical'))
        $canonical=(ConvertTo-Json -InputObject $report -Depth 16 -Compress -ErrorAction Stop)+[string][char]10
        Assert-PaddingValidation ($wire -ceq $canonical -and
            (Test-PaddingValidationUInt $report.version 1) -and $report.version -eq 1 -and
            (Test-PaddingValidationString $report.kind 'ucrt_padding_observation_v1') -and
            (Test-PaddingValidationString $report.purpose 'build_input_error_site_only'))
        foreach($field in @('qualified','linkQualification','closureComplete')){
            Assert-PaddingValidation ($report.$field -is [bool] -and -not $report.$field)
        }
        Assert-PaddingValidation ($report.captureComplete -is [bool])
        Assert-PaddingValidationSummary $report.selfchecks 'ucrt_padding_first_v1' 24
        $proofKeys=@('module','first','parentFirst','reader','supervisor','roster','predecessorSnapshot','predecessorProcess','predecessorResult','predecessorRootReview','descriptor')
        Assert-PaddingValidation ((Test-PaddingValidationFields $ExpectedProofs $proofKeys) -and
            (Test-PaddingValidationFields $report.proofs $proofKeys))
        foreach($key in $proofKeys){
            Assert-PaddingValidation ((Test-PaddingValidationHex $ExpectedProofs.$key) -and
                (Test-PaddingValidationHex $report.proofs.$key) -and $report.proofs.$key -ceq $ExpectedProofs.$key)
        }
        Assert-PaddingValidationPin $ExpectedPin
        Assert-PaddingValidationPin $report.input
        foreach($key in @('name','rootIndex','sourceSlot','bytes','expectedSha256','rootIdentity','leafIdentity')){
            Assert-PaddingValidation ($report.input.$key -ceq $ExpectedPin.$key)
        }
        $prior=$report.priorRefusal
        Assert-PaddingValidation ((Test-PaddingValidationFields $prior @('kind','site','memberIndex','memberOffset')) -and
            (Test-PaddingValidationString $prior.kind 'LibraryInputsFormat') -and
            (Test-PaddingValidationString $prior.site 'archive_padding_byte') -and
            (Test-PaddingValidationUInt $prior.memberIndex 4) -and $prior.memberIndex -eq 4 -and
            (Test-PaddingValidationUInt $prior.memberOffset 98452) -and $prior.memberOffset -eq 98452)
        $full=Test-PaddingValidationIo $report.io
        if($report.captureComplete){
            Assert-PaddingValidation ((Test-PaddingValidationString $report.status 'complete') -and
                $null -eq $report.critical -and $full -and $report.matchesPriorRefusal -is [bool])
            Assert-PaddingValidationObservation $report.observation
            $target=$report.observation.target
            Assert-PaddingValidation ($report.matchesPriorRefusal -eq ($target.paddingRequired -and $target.paddingByte -ne 10))
        }else{
            $io=$report.io;$code=$report.critical;$zero=($io.reservedInputs -eq 0)
            $framing=@('PaddingSignature','PaddingHeader','PaddingSize','PaddingBounds','PaddingPrefix','PaddingTarget')
            $allowed=$framing+@('PaddingPin','PaddingType','PaddingIdentity','PaddingRead','PaddingHash','PaddingStopped','PaddingClose','PaddingSource')
            Assert-PaddingValidation ((Test-PaddingValidationString $report.status 'stopped') -and
                $null -eq $report.observation -and $null -eq $report.matchesPriorRefusal -and $code -is [string] -and
                $allowed -ccontains $code)
            if($code -ceq 'PaddingPin'){Assert-PaddingValidation $zero}
            elseif($framing -ccontains $code){Assert-PaddingValidation $full}
            elseif($code -ceq 'PaddingType'){Assert-PaddingValidation ($zero -or $full)}
            elseif($code -ceq 'PaddingClose'){
                Assert-PaddingValidation ($io.opened -and -not $io.closed -and
                    $io.verifiedPasses -eq 2 -and $io.actualReadBytes -eq 571176)
            }elseif($code -ceq 'PaddingHash'){
                Assert-PaddingValidation ($io.opened -and $io.actualReadBytes -ge 285588)
            }elseif($code -ceq 'PaddingIdentity' -or $code -ceq 'PaddingRead'){
                Assert-PaddingValidation ($io.reservedInputs -eq 1)
            }
        }
        return $report
    }catch{throw 'InvalidPaddingObservationReport'}
}
