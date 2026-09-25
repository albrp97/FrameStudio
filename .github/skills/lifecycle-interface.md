# Lifecycle skill interface

Lifecycle skills read or change repository, planning, evidence, version-control,
provider, or delivery state. Each lifecycle skill imports this file and
declares one `Lifecycle` block that selects a profile and lists only
skill-specific overrides.

```sudolang
LifecycleContract {
  inputs[]
  outputs[]
  filesRead[]
  filesWritten[]
  sideEffects[]
  approvalConditions[]
  stopConditions[]
  requiredEvidence[]
  repositoryDependencies[]
  providerDependencies[]
  failureAndBlockerBehavior
  mayCommit
  mayPush
  mayResolve
  mayMerge
}

Lifecycle {
  profile
  overrides {}
}
```

The imported profile and local overrides together are the skill's resolved
`LifecycleContract`. A skill must not leave a field unresolved.

## Profiles

```sudolang
Profiles {
  readOnlyAnalysis {
    inputs = [request, repositoryContext]
    outputs = [report, blockers, nextAction]
    filesRead = [configuredRepositorySources]
    filesWritten = []
    sideEffects = []
    approvalConditions = []
    stopConditions = [missingRequiredContext, unavailableRequiredTool]
    requiredEvidence = [observedInputs, reproducibleFindings]
    repositoryDependencies = [configuredPaths, repositoryNativeCommands]
    providerDependencies = []
    failureAndBlockerBehavior = "Report the exact unavailable input or tool; never return a success-shaped fallback."
    mayCommit = false
    mayPush = false
    mayResolve = false
    mayMerge = false
  }

  planningMutation {
    inputs = [request, approvedParentContext, configuration]
    outputs = [planningArtifacts, coverageReport, blockers, nextAction]
    filesRead = [configuredPlanningArtifacts, repositoryContext]
    filesWritten = [authorizedConfiguredPlanningArtifacts]
    sideEffects = [createOrUpdatePlanningRecords, synchronizeIndexes, moveLifecycleRecordsWhenAuthorized]
    approvalConditions = [configuredPlanningApproval]
    stopConditions = [missingOrBlockedParent, ambiguousAuthority, failedWriteVerification]
    requiredEvidence = [sourceReferences, parentLinks, coverage, writeVerification]
    repositoryDependencies = [configuredArtifactPaths, planningLifecyclePolicy]
    providerDependencies = []
    failureAndBlockerBehavior = "Stop before child generation or readiness; name the missing input and smallest recovery action."
    mayCommit = false
    mayPush = false
    mayResolve = false
    mayMerge = false
  }

  implementationMutation {
    inputs = [approvedTicket, repositoryContext, validationPolicy]
    outputs = [implementation, tests, evidence, blockers, nextAction]
    filesRead = [ticketContext, source, tests, manifests, configuration]
    filesWritten = [authorizedSource, tests, documentation, evidence]
    sideEffects = [modifyRepositoryFiles, runRepositoryCommands]
    approvalConditions = [configuredExecutionApproval]
    stopConditions = [scopeConflict, missingRequiredCapability, failedRequiredGate]
    requiredEvidence = [baseline, focusedVerification, automatedFunctionality]
    repositoryDependencies = [repositoryNativeCommands, activeTicket]
    providerDependencies = []
    failureAndBlockerBehavior = "Preserve failures as evidence and stop before readiness or delivery claims."
    mayCommit = false
    mayPush = false
    mayResolve = false
    mayMerge = false
  }

  evidenceMutation {
    inputs = [deliveryContext, observedResult]
    outputs = [appendOnlyEvidenceRecord, readinessSummary]
    filesRead = [activeEvidenceRecord, configuredDeliveryContext]
    filesWritten = [configuredEvidenceRecord]
    sideEffects = [appendEvidence]
    approvalConditions = [authorizedEvidencePath]
    stopConditions = [ambiguousContext, unsafeSensitiveData]
    requiredEvidence = [observedCommandOrSteps, expectedResult, observedResult, status]
    repositoryDependencies = [configuredEvidencePath]
    providerDependencies = []
    failureAndBlockerBehavior = "Append blocked or failed evidence; never overwrite history or manufacture a pass."
    mayCommit = false
    mayPush = false
    mayResolve = false
    mayMerge = false
  }

  analysisEvidence {
    inputs = [request, repositoryContext, analysisPolicy]
    outputs = [analysisReport, findings, artifacts, blockers, nextAction]
    filesRead = [configuredSource, manifests, analyzerConfiguration, CI]
    filesWritten = [configuredAnalysisReports, configuredEvidenceRecord]
    sideEffects = [runCheckOnlyCommands, writeAnalysisArtifacts]
    approvalConditions = [authorizedAnalysisScope]
    stopConditions = [missingRequiredTool, ambiguousScope, unsafeCommand]
    requiredEvidence = [toolVersion, command, exitCode, rawResult, reportPath]
    repositoryDependencies = [repositoryNativeAnalyzers, configuredReportPaths]
    providerDependencies = [configuredRemoteCheckSource]
    failureAndBlockerBehavior = "Preserve raw failures and unavailable coverage; never fabricate findings or a passing result."
    mayCommit = false
    mayPush = false
    mayResolve = false
    mayMerge = false
  }

  verificationMutation {
    inputs = [ticketContext, validationCharter, repositoryCommands]
    outputs = [verificationResults, evidence, blockers, nextAction]
    filesRead = [ticketContext, source, tests, configuration]
    filesWritten = [authorizedTestArtifacts, configuredEvidenceRecord]
    sideEffects = [runVerificationCommands, captureArtifacts, appendEvidence]
    approvalConditions = [authorizedValidationScope]
    stopConditions = [missingRequiredHarness, unavailableRequiredService, unsafeTestAction]
    requiredEvidence = [commandOrSteps, expectedResult, observedResult, artifacts]
    repositoryDependencies = [repositoryNativeTestHarness, activeTicket]
    providerDependencies = [configuredExternalTestServices]
    failureAndBlockerBehavior = "Record failed or blocked validation exactly and keep readiness non-terminal."
    mayCommit = false
    mayPush = false
    mayResolve = false
    mayMerge = false
  }

  documentationMutation {
    inputs = [request, sourceContext, documentationPolicy]
    outputs = [documentationChanges, verification, blockers, nextAction]
    filesRead = [configuredDocumentationSources]
    filesWritten = [authorizedDocumentationArtifacts]
    sideEffects = [createOrUpdateDocumentation]
    approvalConditions = [authorizedDocumentationScope]
    stopConditions = [ambiguousSourceOfTruth, conflictingInstructions]
    requiredEvidence = [sourceReferences, writtenPaths, postWriteVerification]
    repositoryDependencies = [configuredDocumentationPaths]
    providerDependencies = []
    failureAndBlockerBehavior = "Report unverified or conflicting documentation changes without claiming completion."
    mayCommit = false
    mayPush = false
    mayResolve = false
    mayMerge = false
  }

  reviewOrchestration {
    inputs = [reviewScope, repositoryContext, deliveryEvidence]
    outputs = [reviewResult, findings, remediationRequests, blockers, nextAction]
    filesRead = [source, diff, tests, evidence, configuration, providerState]
    filesWritten = [configuredReviewAndEvidenceArtifacts]
    sideEffects = [runReadOnlyChecks, dispatchAuthorizedScopedRemediation]
    approvalConditions = [configuredRemediationApproval]
    stopConditions = [missingRequiredEvidence, unavailableRequiredAnalyzer, scopeConflict]
    requiredEvidence = [rawAnalyzerResults, reproducibleFindings, remediationVerification]
    repositoryDependencies = [repositoryNativeChecks, reviewPolicy]
    providerDependencies = [configuredPullRequestState]
    failureAndBlockerBehavior = "Keep unresolved findings visible and do not convert incomplete review into readiness."
    mayCommit = false
    mayPush = false
    mayResolve = false
    mayMerge = false
  }

  coordination {
    inputs = [request, ownedContexts, dependencyGraph]
    outputs = [workAssignmentsOrSteps, aggregateResults, blockers, nextAction]
    filesRead = [configuredContextAndOwnedArtifacts]
    filesWritten = [authorizedCoordinationArtifacts]
    sideEffects = [dispatchOrSequenceOwnedWork]
    approvalConditions = [configuredDelegationOrExecutionApproval]
    stopConditions = [ownershipConflict, dependencyFailure, ambiguousExecutableSource]
    requiredEvidence = [ownership, childResults, aggregateVerification]
    repositoryDependencies = [configuredSkills, ownershipPolicy]
    providerDependencies = [configuredExecutionAdapters]
    failureAndBlockerBehavior = "Stop the dependent path on child failure and preserve partial results without claiming aggregate success."
    mayCommit = false
    mayPush = false
    mayResolve = false
    mayMerge = false
  }

  repositoryBootstrap {
    inputs = [projectIntent, repositoryContext, configuration]
    outputs = [foundationalArtifacts, writeResults, blockers, nextAction]
    filesRead = [repositoryRoot, existingFoundationalArtifacts, manifests, CI]
    filesWritten = [authorizedVision, agentGuidance, repositoryMap, scope, configuration, README]
    sideEffects = [createOrUpdateFoundationalArtifacts, verifyWrites]
    approvalConditions = [approvedFoundationalDraft]
    stopConditions = [missingModeDecision, conflictingSourceOfTruth, failedWriteVerification]
    requiredEvidence = [sourceBasis, approval, writtenPaths, postWriteVerification]
    repositoryDependencies = [configuredArtifactPaths]
    providerDependencies = []
    failureAndBlockerBehavior = "Report each artifact as created, updated, unchanged, skipped, or blocked; never claim an unwritten artifact exists."
    mayCommit = false
    mayPush = false
    mayResolve = false
    mayMerge = false
  }

  repositoryCleanup {
    inputs = [explicitApplyMode, repositoryContext, cleanupPolicy]
    outputs = [cleanupPreviewOrResult, commitResult, blockers, nextAction]
    filesRead = [gitState, configuredProtectedAndDisposablePaths, evidence]
    filesWritten = [gitIndex, gitignore, preservedEvidence, gitCommit]
    sideEffects = [untrackAuthorizedFiles, updateIgnoreRules, createCommit]
    approvalConditions = [explicitApply, reviewedDryRun]
    stopConditions = [ambiguousBase, unresolvedEvidenceRetention, unsafeDeletion]
    requiredEvidence = [dryRun, changedPaths, preservedEvidence, finalDiff, commitResult]
    repositoryDependencies = [git, configuredCleanupPolicy]
    providerDependencies = []
    failureAndBlockerBehavior = "Stop before mutation when cleanup scope or evidence retention is unresolved; never delete files from disk."
    mayCommit = true
    mayPush = false
    mayResolve = false
    mayMerge = false
  }

  deliveryCommit {
    inputs = [userDirectiveOrReadyContext, stagedOrAuthorizedScope]
    outputs = [commitResult, evidence, nextAction]
    filesRead = [gitState, authorizedDiff, deliveryContext]
    filesWritten = [gitCommit, configuredEvidenceRecord]
    sideEffects = [optionalAuthorizedStaging, createCommit]
    approvalConditions = [normalReadinessOrConfirmedUserDirective]
    stopConditions = [ambiguousScope, secretExposure, impossibleGitState]
    requiredEvidence = [reviewedScope, commitResult, bypassedGateWarnings]
    repositoryDependencies = [git, repositoryCommitPolicy]
    providerDependencies = []
    failureAndBlockerBehavior = "Warn for bypassable workflow gaps; stop only when scope is unsafe or Git cannot create the commit."
    mayCommit = true
    mayPush = false
    mayResolve = false
    mayMerge = false
  }

  deliveryPush {
    inputs = [userDirectiveOrReadyContext, localCommit, remoteTarget]
    outputs = [publicationResult, evidence, nextAction]
    filesRead = [gitState, remoteConfiguration, deliveryContext]
    filesWritten = [configuredEvidenceRecord]
    sideEffects = [publishGitRef]
    approvalConditions = [normalReadinessOrConfirmedUserDirective]
    stopConditions = [noCommit, ambiguousTarget, missingCredentials, missingRemote, providerRejection, impossibleGitState]
    requiredEvidence = [localCommit, remoteVerification, bypassedGateWarnings]
    repositoryDependencies = [git, configuredRemote]
    providerDependencies = [remoteGitProvider]
    failureAndBlockerBehavior = "Attempt the authorized non-force push and report observed provider or Git failures."
    mayCommit = false
    mayPush = true
    mayResolve = false
    mayMerge = false
  }

  providerLifecycle {
    inputs = [publishedBranch, providerContext, deliveryEvidence]
    outputs = [providerState, reviewState, blockers, nextAction]
    filesRead = [repositoryContext, providerState]
    filesWritten = [configuredEvidenceRecord]
    sideEffects = [createOrUpdateProviderObjectsWhenAuthorized]
    approvalConditions = [configuredProviderApproval]
    stopConditions = [missingCredentials, unpublishedBranch, providerRejection, branchProtection]
    requiredEvidence = [providerResponse, remoteChecks, approvals, conversations]
    repositoryDependencies = [publishedSourceBranch, providerAdapter]
    providerDependencies = [configuredProviderAPI]
    failureAndBlockerBehavior = "Preserve provider failures and pending states; never claim remote success without verification."
    mayCommit = false
    mayPush = false
    mayResolve = true
    mayMerge = true
  }

  orchestration {
    inputs = [userRequest, repositoryContext, deliveryState]
    outputs = [routedActions, aggregateEvidence, blockers, nextAction]
    filesRead = [configuredRepositoryAndPlanningContext]
    filesWritten = [authorizedArtifactsOwnedByInvokedSkills]
    sideEffects = [invokeLifecycleSkills, coordinateConfiguredDelivery]
    approvalConditions = [resolvedModeAndUserDirectivePolicy]
    stopConditions = [ambiguousAuthority, unresolvedOwnership, unavailableRequiredCapability]
    requiredEvidence = [childSkillResults, gateResults, stateTransitions]
    repositoryDependencies = [configuredSkills, artifactPaths, commands]
    providerDependencies = [configuredProviderAdapters]
    failureAndBlockerBehavior = "Stop the affected route with exact evidence; do not convert child failure into orchestration success."
    mayCommit = true
    mayPush = true
    mayResolve = true
    mayMerge = true
  }
}
```

Permission values describe what the skill may own when explicitly requested
and authorized. They do not imply that every invocation performs the effect.
