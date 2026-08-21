# aidd-push

`aidd-push` safely publishes an already-reviewed local commit to its
configured remote branch. It does not stage, commit, force-push, create a PR,
or merge anything by default.

## Usage

Use `/push` after `/commit` when the local branch is unpublished or ahead of
its upstream. After the remote ref is verified, the workflow routes to
`/aidd-pr` when repository policy requires a pull request.

## When to use

- A successful local commit needs to be published
- A review-fix commit must be sent to an existing PR branch
- Remote CI or a configured preview requires the branch to be pushed
