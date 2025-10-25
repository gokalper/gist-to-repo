# Gist to Repo Sync Action

Sync files from a GitHub Gist into your repository with flexible mapping strategies.

## Features

- ✅ Multiple file mapping strategies
- ✅ Configurable merge strategies (overwrite by default)
- ✅ Auto-commit with customizable messages
- 🚧 Pull request support (coming soon)
- 🚧 Timestamp-based merging (coming soon)

## Usage Examples

### 1. Same Names Strategy (Default)

Syncs all files from Gist to a target directory, keeping the same filenames:

```yaml
- name: Sync Gist to Repo
  uses: your-username/gist-to-repo-sync@v1
  with:
    gist_token: ${{ secrets.GIST_TOKEN }}
    gist_id: 'abc123def456'
    target_path: './config/'
```

This will copy `config.json` from Gist to `./config/config.json` in your repo.

### 2. Explicit Mapping Strategy

Define exactly where each Gist file should go:

```yaml
- name: Sync with Explicit Mapping
  uses: your-username/gist-to-repo-sync@v1
  with:
    gist_token: ${{ secrets.GIST_TOKEN }}
    gist_id: 'abc123def456'
    mapping_strategy: 'explicit'
    file_mappings: |
      {
        "config.json": "src/app/config.json",
        "secrets.env": ".env.production",
        "readme.md": "docs/gist-readme.md"
      }
```

### 3. Prefix Strategy

Add or remove a prefix from filenames:

```yaml
- name: Sync with Prefix Removal
  uses: your-username/gist-to-repo-sync@v1
  with:
    gist_token: ${{ secrets.GIST_TOKEN }}
    gist_id: 'abc123def456'
    mapping_strategy: 'prefix'
    file_prefix: 'gist-'
    target_path: './synced/'
```

If Gist contains `gist-config.json`, it will be saved as `./synced/config.json`.

### 4. All to Directory Strategy

Copy all files to a specific directory:

```yaml
- name: Sync All Files
  uses: your-username/gist-to-repo-sync@v1
  with:
    gist_token: ${{ secrets.GIST_TOKEN }}
    gist_id: 'abc123def456'
    mapping_strategy: 'all_to_directory'
    target_path: './gist-backup/'
```

### 5. Skip Existing Files

Don't overwrite files that already exist:

```yaml
- name: Sync Without Overwriting
  uses: your-username/gist-to-repo-sync@v1
  with:
    gist_token: ${{ secrets.GIST_TOKEN }}
    gist_id: 'abc123def456'
    merge_strategy: 'skip_existing'
    target_path: './config/'
```

### 6. Custom Commit Message

```yaml
- name: Sync with Custom Commit
  uses: your-username/gist-to-repo-sync@v1
  with:
    gist_token: ${{ secrets.GIST_TOKEN }}
    gist_id: 'abc123def456'
    commit_message: 'chore: update config from Gist {gist_id} [skip ci]'
    git_user_name: 'Config Bot'
    git_user_email: 'bot@example.com'
```

## Complete Workflow Example

```yaml
name: Sync Config from Gist

on:
  schedule:
    # Run every day at midnight
    - cron: '0 0 * * *'
  workflow_dispatch: # Allow manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3
        
      - name: Sync Gist to Repo
        uses: your-username/gist-to-repo-sync@v1
        with:
          gist_token: ${{ secrets.GIST_TOKEN }}
          gist_id: 'abc123def456'
          mapping_strategy: 'explicit'
          file_mappings: |
            {
              "production.json": "config/production.json",
              "staging.json": "config/staging.json"
            }
          merge_strategy: 'overwrite'
          commit_message: 'chore: sync config from Gist'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `gist_token` | Personal Access Token with Gist read access | Yes | - |
| `gist_id` | ID of the Gist to sync from | Yes | - |
| `mapping_strategy` | How to map files: `same_names`, `explicit`, `prefix`, `all_to_directory` | No | `same_names` |
| `file_mappings` | JSON mapping for explicit strategy | No | `{}` |
| `target_path` | Target directory in repo | No | `./` |
| `file_prefix` | Prefix for prefix strategy | No | `''` |
| `merge_strategy` | `overwrite`, `skip_existing`, `newer_only` (future) | No | `overwrite` |
| `create_pr` | Create PR instead of direct commit (future) | No | `false` |
| `commit_message` | Custom commit message (supports `{gist_id}`, `{actor}`, `{ref}`) | No | `Sync from Gist {gist_id}` |
| `git_user_name` | Git user name for commit | No | `github-actions[bot]` |
| `git_user_email` | Git user email for commit | No | `github-actions[bot]@users.noreply.github.com` |

## Setup

1. Create a Personal Access Token with `gist` read access
2. Add it to your repository secrets as `GIST_TOKEN`
3. Get your Gist ID from the URL (e.g., `https://gist.github.com/username/ABC123` → ID is `ABC123`)
4. Configure your workflow as shown above

## Future Features

- 🚧 Pull request creation instead of direct commits
- 🚧 Timestamp-based merge strategy (only sync if Gist is newer)
- 🚧 Bi-directional sync
- 🚧 File filtering with glob patterns
- 🚧 Dry-run mode