# HCL style and module design

Detail behind the defaults in SKILL.md, for writing or reviewing
non-trivial configurations.

## Naming

- Resource/module/variable/output names: `snake_case`, nouns, no repetition
  of the resource type (`aws_subnet.private`, not `aws_subnet.private_subnet`).
- Cloud-side names and tags: build from stable inputs, usually in a local —
  `local.name_prefix = "${var.project}-${var.environment}"` — so every
  resource names itself consistently.
- Variables: name for meaning, not type (`retention_days`, not `number1`);
  booleans read as predicates (`enable_logging`, `create_dns_record`).
- Outputs: name from the consumer's point of view (`vpc_id`,
  `bucket_arn`), and describe what it is, not how it was made.

## Expression hygiene

- `locals` for any expression used twice, or once but unreadable inline.
- Prefer `try()` and `coalesce()` over nested conditionals; prefer
  splat/`for` expressions over element-by-index.
- String templates only when interpolating (`"${a}-${b}"`); a bare
  reference is just `var.a`.
- `jsonencode()`/`yamlencode()` over heredoc JSON/YAML — they get syntax
  checking and canonical formatting.
- Give every non-obvious ternary or `for` expression a one-line comment
  saying what it produces, not how.

## for_each patterns

```hcl
variable "buckets" {
  description = "Buckets to create, keyed by logical name."
  type = map(object({
    versioned  = optional(bool, true)
    kms_key_id = optional(string)
  }))
}

resource "aws_s3_bucket" "this" {
  for_each = var.buckets
  bucket   = "${local.name_prefix}-${each.key}"
}
```

- Key `for_each` maps by a **stable logical name**, never by an attribute
  of another resource unknown at plan time (that fails with "invalid
  for_each argument") and never by list index.
- Convert a list to a set for simple cases:
  `for_each = toset(var.availability_zones)`.
- The zero-or-one pattern: `count = var.create_thing ? 1 : 0`, referenced
  as `resource.thing[0]`; on module calls the same works with `count` on
  the `module` block.
- `dynamic` blocks are for repeated *nested* blocks only:

```hcl
dynamic "ingress" {
  for_each = var.ingress_rules
  content {
    from_port = ingress.value.port
    to_port   = ingress.value.port
    protocol  = "tcp"
  }
}
```

Don't reach for `dynamic` to save typing two static blocks — it costs
readability and only pays off when the set genuinely varies.

## Meta-arguments worth knowing

- `lifecycle`:
  - `prevent_destroy = true` — irreplaceable resources (data stores, KMS).
  - `create_before_destroy = true` — resources referenced by name elsewhere
    (launch templates, certificates) so replacement doesn't leave a gap.
  - `ignore_changes = [...]` — attributes mutated outside Terraform
    (autoscaling desired_count, externally-managed tags). Every entry is
    accepted drift; comment why.
  - `precondition`/`postcondition` — see testing-and-ci.md.
- `provider =` on a resource selects an aliased provider (multi-region,
  multi-account). Aliases are declared once in the root and passed to
  modules via the `providers` map on the module call.

## Module design

A good module has an opinion. Checklist:

- **Small surface**: expose the decisions consumers must make; default the
  rest. Twenty variables that just forward provider arguments is a wrapper,
  not a module.
- **No provider blocks** inside modules — declare `required_providers`
  only. Provider config (region, credentials, default tags) belongs to the
  root; roots pass aliased providers down with `providers = { aws = aws.eu }`.
- **Outputs are the contract**: output every id/arn/name a consumer could
  plausibly need; changing or removing an output is a breaking change.
- **Compose, don't nest deep**: roots call modules; modules may call small
  utility modules; three levels down nobody can trace a value.
- **Version everything**: registry sources with `version = "~> 4.0"`; git
  sources with `?ref=v1.2.0` (tag) or a full SHA. A branch ref is not a pin.
- Layout mirrors a root module (`main.tf`, `variables.tf`, `outputs.tf`,
  `versions.tf`, plus `README.md`); `terraform-docs` generates the
  input/output tables if the repo uses it.

## Environments

Prefer one root module per environment (`envs/dev`, `envs/prod`, each a
thin root calling shared modules with different values) or per-env tfvars
applied by CI, over CLI workspaces. Workspaces share one backend and one
code path, which makes "prod is different" invisible in review; they suit
many identical copies (per-PR preview stacks), not dev-vs-prod divergence.

## Anti-patterns to flag in review

- Unpinned providers/modules, or `required_version` pinned exact in a
  shared module.
- `count` used for collections (index-shift recreation risk).
- Secrets in defaults, committed tfvars, or heredoc user_data; state
  backend without encryption.
- Hard-coded IDs/ARNs that a data source could look up.
- One giant root module for the whole estate — blast radius of every plan
  is everything; split along ownership/lifecycle seams.
- `depends_on` where an attribute reference would do.
- Values duplicated across environments instead of defaulted in a module
  or shared tfvars.
- Provider blocks inside reusable modules (breaks `for_each` on the module
  and multi-region use).
