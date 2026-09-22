# State, backends, and refactoring

For configuring/migrating backends, adopting existing infrastructure,
state surgery, and drift.

## Backends

One backend per root module, in `backend.tf`. Backends cannot interpolate
variables — values are literal, or supplied at init time with
`-backend-config` (flags or a `.tfbackend` file), which is how one config
serves several environments.

```hcl
# AWS — native S3 locking (Terraform >= 1.10); DynamoDB locking is deprecated
terraform {
  backend "s3" {
    bucket       = "myorg-tfstate"
    key          = "platform/network/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true
  }
}

# Azure
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "myorgtfstate"
    container_name       = "tfstate"
    key                  = "platform/network.tfstate"
    use_azuread_auth     = true   # RBAC instead of storage access keys
  }
}

# GCP (GCS locks and versions natively)
terraform {
  backend "gcs" {
    bucket = "myorg-tfstate"
    prefix = "platform/network"
  }
}

# HCP Terraform / Terraform Cloud uses a cloud block, not a backend block
terraform {
  cloud {
    organization = "myorg"
    workspaces { name = "platform-network" }
  }
}
```

Requirements whatever the platform: encryption at rest, versioning (state
recovery is "restore the previous object version"), locking, and access
restricted to the pipeline plus break-glass humans — state contains every
sensitive value in plaintext. Give each root module its own `key`/`prefix`.

**Changing backends**: edit the block, then `terraform init -migrate-state`
(copies existing state across; prompts before overwriting).
`-reconfigure` switches **without** copying — only when the new backend
already holds the right state.

Read another root's outputs with `terraform_remote_state` data source, or
better, publish them somewhere neutral (SSM parameters, app config) so
consumers don't need read access to your state.

## Inspecting state

```bash
terraform state list                    # all addresses in state
terraform state show aws_s3_bucket.this # one resource's recorded attributes
terraform output [-json]                # root outputs
terraform show -json tfplan             # machine-readable plan (for review tooling)
```

## Refactoring with config blocks (preferred)

These are declarative, land in review, and show up in `plan`:

```hcl
moved {                     # rename/move without destroy+recreate
  from = aws_instance.app
  to   = aws_instance.web
}

import {                    # adopt an existing resource (Terraform >= 1.5)
  to = aws_s3_bucket.logs
  id = "myorg-logs-bucket"  # id format is per-resource; check provider docs
}

removed {                   # drop from state WITHOUT destroying (>= 1.7)
  from = aws_instance.legacy
  lifecycle { destroy = false }
}
```

Import workflow: write a placeholder `resource` block, add the `import`
block, run `terraform plan` — it shows what the config must say to match
reality (`plan -generate-config-out=generated.tf` drafts it, treat as a
draft) — reconcile until the plan is a no-op, then apply and delete the
import block. Moving resources **between state files**: `removed` (with
`destroy = false`) in the source root + `import` in the destination.

## State surgery (imperative fallback)

`terraform state mv|rm`, `terraform import` (CLI form) mutate state
immediately with no plan and no review. Use only when config blocks can't
express the change or on Terraform < 1.5. Back up first: pull a copy with
`terraform state pull > backup.tfstate` (restore with `state push`).

- Stuck lock after a crashed run: `terraform force-unlock <LOCK_ID>` —
  only after confirming no other run is live.
- Corrupted/lost state: restore the backend's previous object version;
  re-import as the last resort.

## Drift

`terraform plan -refresh-only` shows real-world changes without proposing
config changes; `apply -refresh-only` accepts them into state. Unexpected
diffs in a normal plan mean someone changed infra out-of-band: decide
per-attribute whether to codify the change, revert it via apply, or accept
it permanently with `lifecycle.ignore_changes`. Schedule a plan in CI so
drift is noticed before it bites (see testing-and-ci.md).

## Incident-only flags

- `terraform apply -replace=<addr>` — force recreation of a broken
  resource (replaces deprecated `taint`).
- `terraform plan/apply -target=<addr>` — narrow an emergency fix.
  Follow up with a full clean plan; repeated targeting means the root
  module is too big.
- `terraform destroy` (or `apply -destroy`) — always show the destroy plan
  and get explicit confirmation; check `prevent_destroy` guards first.
