---
name: terraform
description: >-
  Author, review, and operate Terraform / OpenTofu infrastructure-as-code:
  write HCL configurations and reusable modules, pin providers, structure
  variables/outputs/locals, manage remote state and backends, plan and
  apply safely, adopt existing resources with import blocks, refactor with
  moved/removed blocks, and validate with fmt/validate/tflint and
  `terraform test`. Use when the user mentions Terraform, OpenTofu, HCL,
  `.tf` or `.tfvars` files, providers, modules, remote state, tfstate,
  plan/apply/destroy/import, drift, or wants cloud infrastructure
  (AWS/Azure/GCP or any provider) defined, changed, reviewed, or tested as
  code — even if they just say "terraform this" or "write IaC for X".
---

# Terraform / OpenTofu

Everything here applies to Terraform 1.x and OpenTofu alike (substitute
`tofu` for `terraform`); differences are called out where they exist. Work
with whichever binary the project already uses — check `.terraform-version`,
`mise.toml`, CI config, or the lock file before assuming.

## Core loop

```bash
terraform fmt -recursive        # canonical formatting, always safe
terraform init                  # backend + providers; rerun after changing either
terraform validate              # syntax and internal consistency
terraform plan -out=tfplan      # review the diff BEFORE any apply
terraform apply tfplan          # apply exactly the reviewed plan
```

Run `fmt` and `validate` after every edit — they are fast and catch most
mistakes before a human reads the code. Never run `apply` (or `destroy`)
without showing the plan and getting explicit confirmation from the user:
plans mutate real, billable, sometimes irreplaceable infrastructure.
`apply tfplan` beats a bare `apply` because it applies exactly what was
reviewed, not a fresh plan.

## Root module layout

Split by purpose, not by resource count — Terraform reads all `*.tf` in a
directory as one module, so filenames are for humans:

```
main.tf          # resources and module calls (split into <topic>.tf as it grows)
variables.tf     # every input variable
outputs.tf       # every output
versions.tf      # terraform + provider version constraints
providers.tf     # provider configuration (region, tags, auth)
backend.tf       # state backend
locals.tf        # derived values (optional)
terraform.tfvars # environment values — never secrets
```

Commit `.terraform.lock.hcl` (it pins exact provider builds); ignore
`.terraform/`, `*.tfstate*`, `*.tfplan`, and any `*.tfvars` holding
secrets.

## Pin versions

Unpinned configs break on the next provider release. Always declare:

```hcl
terraform {
  required_version = ">= 1.9.0"     # floor only — modules must not pin exact CLI versions
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"            # pessimistic constraint: any 6.x
    }
  }
}
```

Root modules may pin tighter; shared modules should state the loosest
constraint that actually works so consumers aren't boxed in.

## Variables and outputs

Every variable and output gets a `description` and every variable a
`type` — they are the module's API docs. Validate what you can:

```hcl
variable "environment" {
  description = "Deployment environment, used in names and tags."
  type        = string
  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be dev, test, or prod."
  }
}

variable "db_password" {
  description = "Master password for the database."
  type        = string
  sensitive   = true   # hides it from plan output — it is STILL in state
  # no default: secrets never get defaults, and never live in committed tfvars
}
```

`sensitive = true` only redacts CLI output; the value is written to state
in plaintext, so the state backend must be encrypted and access-controlled.
Prefer pulling secrets at apply time (e.g. a secrets-manager data source)
or, on Terraform ≥ 1.10 / OpenTofu ≥ 1.8, `ephemeral` values and
write-only arguments, which never touch state.

## Resources: the defaults that matter

- Name resources for their role, not their type: `aws_instance.web`, not
  `aws_instance.web_instance` (the type is already in the address). Use
  `this` for the single resource a small module exists to create.
- Prefer `for_each` over `count` for collections — `count` addresses by
  index, so removing one item renumbers and **recreates** every later
  resource. Reserve `count` for the boolean "zero or one" pattern.
- Put repeated expressions in `locals`; keep `variable` for actual inputs.
- Use `data` sources to look up things that exist outside this config;
  never hard-code account IDs, AMI IDs, or ARNs that can be looked up.
- `depends_on` is a last resort — reference an attribute instead so the
  dependency is real and visible.
- Guard irreplaceable things: `lifecycle { prevent_destroy = true }` on
  databases, state buckets, KMS keys.

## State discipline

State is the source of truth mapping code to real infrastructure. Rules:

- Use a remote, locking, encrypted backend for anything shared (S3 with
  `use_lockfile = true`, `azurerm`, `gcs`, or HCP Terraform). Local state
  is for throwaway experiments only.
- Never edit a state file by hand, and never run two applies concurrently.
- Refactor with code, not CLI surgery: `moved` blocks for renames,
  `removed` blocks to forget without destroying, `import` blocks to adopt
  existing resources — all reviewable in a plan, unlike
  `terraform state mv/rm` which mutate state immediately.
- `-target` and `-replace` are incident tools, not workflow; a config that
  needs routine targeting is structured wrong.

Open [references/state-and-backends.md](references/state-and-backends.md)
when configuring or migrating a backend, adopting existing infrastructure,
doing state surgery/recovery, or handling drift.

## Modules

Write a module when a pattern repeats with variation or encodes a standard
others must follow — not to wrap a single resource with no opinion. A
module is a directory with the same file layout as a root module, minus
backend/provider config (modules declare `required_providers` but never
`provider` blocks). Pin module sources: registry modules with `version =`,
git sources with `?ref=<tag-or-sha>`.

## Before handing work back

Format and validate every change (`terraform fmt -recursive`,
`terraform validate` — after `terraform init -backend=false` if the real
backend isn't reachable). Run `tflint` and any repo-configured scanners
(trivy, checkov) when they are installed. Show the user the `plan` diff
for anything that will be applied.

## References

Open these only when the task needs them:

- [references/style-and-modules.md](references/style-and-modules.md) —
  when writing or reviewing non-trivial HCL: naming and layout detail,
  module design, for_each/dynamic patterns, meta-arguments, anti-patterns.
- [references/state-and-backends.md](references/state-and-backends.md) —
  when touching backends, workspaces, state commands, import/moved/removed
  blocks, drift, or state recovery.
- [references/testing-and-ci.md](references/testing-and-ci.md) — when
  writing `terraform test` suites, check/precondition blocks, or wiring
  plan/apply into CI pipelines.
