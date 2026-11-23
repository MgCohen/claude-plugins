This is a default decision ({{reason}}). The user did not answer yet and will review it later.
Before you act on it, keep the work of this decision apart, so that the user can approve or refuse it alone. Run each command in your working folder:
1. Commit your current work on the current branch.
2. Run `orch decision start {{decision}}`. It makes the decision branch on top of the current branch and checks it out.
3. Make the work of this decision on that branch, and commit it.
4. Run `orch decision pr {{decision}}`. It pushes the branch and opens a draft PR, if the repository has a GitHub remote.
5. Call mcp__orch__report with state working, and give the branch and the PR link in details.
Continue your later work on top of this branch.
