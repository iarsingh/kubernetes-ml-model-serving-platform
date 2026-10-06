# kubernetes-ml-model-serving-platform — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does kubernetes-ml-model-serving-platform address, and what can you demonstrate?

Pass when probes and hpa are true and the image is pinned.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/k8sml/main.py`](src/k8sml/main.py): Implementation or supporting configuration.
- [`src/k8sml/ops.py`](src/k8sml/ops.py): Implementation or supporting configuration.
- [`src/k8sml/gate.py`](src/k8sml/gate.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`src/k8sml/__init__.py`](src/k8sml/__init__.py): Implementation or supporting configuration.
- [`Dockerfile`](Dockerfile): Container build/service configuration.
- [`Makefile`](Makefile): Implementation or supporting configuration.
- [`docker-compose.yml`](docker-compose.yml): Container build/service configuration.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `check` and explain the decision it makes?

The main walkthrough here is `check(body)` in [`src/k8sml/gate.py`](src/k8sml/gate.py#L5).

```python
def check(body):
    if not isinstance(body, dict):
        raise InputError("body must be an object")
    failed = []

    image = str(body.get("image", ""))
    if image.endswith(":latest") or image == "latest":
        failed.append("image_tag_latest")

    if not body.get("probes"): failed.append("missing_probes")
    if not body.get("hpa"): failed.append("missing_hpa")
    return {"passed": not failed, "failed": failed, "applied": False}
```

The implementation calls `InputError`, `body.get`, `failed.append`, `image.endswith`, `isinstance`, `str`. In an interview, trace those calls in execution order using a fixture input.

## 4. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `InputError('body must be an object')` in [`src/k8sml/gate.py`](src/k8sml/gate.py#L7).
- `HTTPException(status_code=422, detail=str(exc))` in [`src/k8sml/main.py`](src/k8sml/main.py#L19).
- `HTTPException(status_code=404, detail='workspace not found')` in [`src/k8sml/ops.py`](src/k8sml/ops.py#L77).
- `HTTPException(status_code=404, detail='job not found')` in [`src/k8sml/ops.py`](src/k8sml/ops.py#L100).
- `HTTPException(status_code=404, detail='job not found')` in [`src/k8sml/ops.py`](src/k8sml/ops.py#L109).
- `HTTPException(status_code=403, detail='production apply is disabled in this lab')` in [`src/k8sml/ops.py`](src/k8sml/ops.py#L113).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 5. Which test would you use to demonstrate correctness?

[`tests/test_gate.py`](tests/test_gate.py#L7) contains `test_pass_and_fail`:

```python
def test_pass_and_fail():
    good = client.post("/check", json={'probes': True, 'hpa': True, 'image': 'serve:1.0.0'}).json()
    assert good["passed"] is True
    assert good["applied"] is False
    bad = client.post("/check", json={'probes': True, 'hpa': True, 'image': 'serve:latest'}).json()
    assert bad["passed"] is False
    assert "image_tag_latest" in bad["failed"]
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 6. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/k8sml/main.py`](src/k8sml/main.py#L10).
- `POST /check` → `post_check` in [`src/k8sml/main.py`](src/k8sml/main.py#L15).
- `GET /readyz` → `readyz` in [`src/k8sml/ops.py`](src/k8sml/ops.py#L74).
- `POST /workspaces` → `create_workspace` in [`src/k8sml/ops.py`](src/k8sml/ops.py#L80).
- `GET /workspaces` → `list_workspaces` in [`src/k8sml/ops.py`](src/k8sml/ops.py#L98).
- `POST /workspaces/{workspace_id}/jobs` → `create_job` in [`src/k8sml/ops.py`](src/k8sml/ops.py#L106).
- `GET /jobs/{job_id}` → `get_job` in [`src/k8sml/ops.py`](src/k8sml/ops.py#L130).
- `POST /jobs/{job_id}/approve` → `approve_job` in [`src/k8sml/ops.py`](src/k8sml/ops.py#L140).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 7. Where does state live, and what happens with multiple workers?

Module-level containers include `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS` in [`src/k8sml/ops.py`](src/k8sml/ops.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 8. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 9. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 10. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 11. What is the input-to-output contract of `check`?

In [`src/k8sml/gate.py`](src/k8sml/gate.py#L5), `check(body)` receives the inputs. The function computes these intermediate values:

- `failed = []`
- `image = str(body.get('image', ''))`

Its result is defined by:

- `{'passed': not failed, 'failed': failed, 'applied': False}`

## 12. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/k8sml/gate.py`](src/k8sml/gate.py#L5) branches on:

- `not isinstance(body, dict)`
- `image.endswith(':latest') or image == 'latest'`
- `not body.get('probes')`
- `not body.get('hpa')`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## 13. What does the operations plane add, and where is its limit?

[`src/k8sml/ops.py`](src/k8sml/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.
