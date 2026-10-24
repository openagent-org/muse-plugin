# Install OpenAgent: Muse

This guide is for installing, updating, or repairing OpenAgent in **Muse (the muse.ai consumer application)**. If the current host is not Muse, stop installation; do not apply installation methods for Muse Code or another client.

When the user requests installation, carry out the steps below without asking again whether to begin; use Muse's native entry points when user sign-in or approval is required. If the user only asks to read or review the guide, do not install anything.

## 1. Read the installation materials online

Download all ten core files below in full from the official `openagent-org/muse-plugin` repository: prefer `https://github.com/openagent-org/muse-plugin.git`, with `https://gitee.com/openagent-org/muse-plugin.git` as the fallback. The installation script retrieves the compressed COS SDK archive according to the lockfile, so the user does not need to upload attachments or archives.

Download directly from the `rel` URLs in the table. Only after a DNS, connection, timeout, interrupted-transfer, or HTTP 5xx failure, confirm that the original request has ended and switch sources once without asking the user to choose a network region. Keep the same repository, `rel` branch, and relative path when switching; the Gitee download pattern is `https://gitee.com/openagent-org/muse-plugin/raw/rel/<relative-path>`. Stop if the fallback fails; do not switch repeatedly.

Do not switch sources for denied permission or approval, certificate errors, HTTP 401/403/404/429/451, checksum or content validation failures, syntax errors, or installation errors; stop and report them. Reject GitHub redirects. Gitee Raw may redirect once to HTTPS `raw.giteeusercontent.com` only after verifying that the repository, `rel` branch, and file path are unchanged. Preserve only the signed query returned by the official server; do not construct or rewrite it.

| Material | GitHub rel download URL |
| --- | --- |
| Connection configuration | [openagent-connection.json](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/openagent-connection.json) |
| Task routing | [openagent-first-task-router/SKILL.md](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-first-task-router/SKILL.md) |
| Result delivery reference | [result-validation-and-delivery.md](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-first-task-router/references/result-validation-and-delivery.md) |
| Usage guidance | [openagent-guide-agent/SKILL.md](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-guide-agent/SKILL.md) |
| Find an Agent | [openagent-search-agent/SKILL.md](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-search-agent/SKILL.md) |
| Run an Agent | [openagent-run-agent/SKILL.md](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-run-agent/SKILL.md) |
| COS upload script | [openagent-run-agent/scripts/cos_upload.cjs](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-run-agent/scripts/cos_upload.cjs) |
| COS dependency lockfile | [openagent-run-agent/scripts/cos_sdk.lock.json](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-run-agent/scripts/cos_sdk.lock.json) |
| COS SDK archive installation script | [install-vendor.py](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/install-vendor.py) |
| Account queries | [openagent-query-account/SKILL.md](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-query-account/SKILL.md) |

Use only the `rel` branch of these two official sources and the relative paths from the table. Preserve the complete original JSON. Do not save an HTML login or error page, incomplete content, or a Skill without a name or description as a skill; if usable content is unavailable, stop and report the issue. Each of the five Skill names must match its directory name; the connection endpoint must be `https://openagent.org/mcp/v1/open-agent`.

## 2. Connect MCP and authorize access

Read Muse's current Custom Connector management instructions and use its actual creation or update entry point. Prefer reusing or repairing an existing OpenAgent or Oasn Open Agent connection, and preserve other connections. The connection JSON provides parameters; it is not an official Muse manifest. Do not import it directly or guess private APIs.

Use the name, endpoint, scope, and metadata URLs in the JSON to configure **Streamable HTTP + an OAuth public client**: use Authorization Code + PKCE S256 with `token_endpoint_auth_method=none`; no client secret is required. Discover authentication endpoints through the public metadata, and verify that the resource is the full MCP URL and the issuer is `https://openagent.org`. If the host supports custom headers, use the headers in the JSON; if it does not, still select OAuth instead of switching to an anonymous connection.

Use the actual, complete callback URL Muse provides for this attempt. Do not hardcode a previously observed value from the JSON as the callback. The user must sign in and consent personally. Leave credential storage and refresh to Muse's security components; do not write credentials into the chat, Skills, or ordinary files, and do not read tokens from other clients.

If authentication fails or its result is unknown, stop and report the issue; do not independently replay registration, code exchange, or refresh. If the response is `redirect_uri is not allowed`, explain that the server has not yet allowed the callback and a maintainer must address it. Do not rewrite the callback to bypass the restriction.

## 3. Verify tools and the account

Run `tools/list`, read the actual tool names and schemas, and confirm that the following tools are available. If the host adds a prefix, use the actual names:

`openagent_search`, `openagent_run`, `openagent_user_guide`, `openagent_account_credits`, `openagent_wait_for_selection`, `openagent_progress`, `openagent_file_upload`, `openagent_stop_run`.

Call `openagent_account_credits({})` once. Confirm that authorization works only after this call succeeds without an error; Connected status, HTTP 200, or the tool list cannot replace account verification. If tools are missing or the call fails, report the specific issue. Do not automatically run an Agent to verify installation.

## 4. Install the five Skills

1. Read Muse's current persistent skill management instructions and confirm the actual save and load entry points. Do not guess skill directories or registration commands.
2. Install all five complete SKILL.md files separately, preserving their names, descriptions, bodies, and relative directory structure. Save the delivery reference as `references/result-validation-and-delivery.md` under the routing Skill. Save the COS Node.js script and dependency lockfile as `scripts/cos_upload.cjs` and `scripts/cos_sdk.lock.json` under the execution Skill, keeping them in the same directory. The fixed-version COS Node.js SDK and its dependencies are distributed as `scripts/cos_sdk.cjs.gz`; retrieve this archive using the installation script below. Task uploads require Node.js 20+. On the first upload, verify the SHA-256 and size of the compressed archive and decompressed bundle, then extract it into a writable `scripts/.cos-sdk/node_modules/<archive SHA-256>/` directory. Subsequent processes verify and reuse that directory, rebuild it from the archive if damaged, and preserve caches for other versions. Uploads do not search for a host SDK or `node_modules`, run `npm install`, or download dependencies. If the archive is missing, verification fails, or the cache is not writable, stop and repair the plugin installation. Use the actual tool names from the verified connection. Do not merge the files into one Skill, save only summaries, or discard the reference, scripts, lockfile, or compressed archive.
3. Update an existing Skill with the same name from this source in place, preserving its existing `scripts/.cos-sdk/` cache. If content with the same name comes from another source, stop before overwriting it. After saving, read back and load each Skill, verify its source and complete content, and confirm that the routing Skill can read the delivery reference and hand off to the other four Skills. Downloading files, reading them in the current conversation, or retaining them in ordinary memory does not count as persistent installation.
4. Only after all five new Skills have been verified successfully, use the actual skill management entry point to disable or remove the old single `openagent` Skill from this source. If its source cannot be confirmed or it cannot be disabled, report the status and preserve other skills, MCP connectors, and user files.

After saving the execution Skill in step 2 of this section, run the downloaded `install-vendor.py` once with Python 3.9+. Replace both paths with the actual absolute paths to the downloaded script and the persistent execution Skill. If the destination directory is unknown, stop instead of guessing a path:

```bash
python3 -I -S '<actual absolute path to install-vendor.py>' --scripts-dir '<actual absolute path to openagent-run-agent/scripts>'
```

The installation script first downloads the archive from the fixed GitHub `rel` URL `https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-run-agent/scripts/cos_sdk.cjs.gz`. Only for the network failures above, it retries once at `https://gitee.com/openagent-org/muse-plugin/raw/rel/skills/openagent-run-agent/scripts/cos_sdk.cjs.gz`; Gitee may redirect once to its official CDN over HTTPS with the same path. The downloaded lockfile identifies the exact archive through the SHA-256 and size of both the compressed archive and decompressed bundle. All checks must pass before an atomic write; validation failures do not trigger fallback. A valid existing archive is reused without network access, preserving the extracted cache and other files. The script must return `SDK_ARCHIVE_READY` before Skill installation can pass acceptance. Run this script only during installation or updates; task uploads do not call it. The extracted cache is written only on the first upload. During updates, preserve unverified old Python scripts and archives instead of deleting them by filename.

If no persistent skill entry point can be confirmed, explicitly report "MCP connected; persistent Skill installation incomplete." Do not claim that the Skills will automatically take effect in future conversations.

## 5. Complete installation

Briefly report the actual results of the MCP connection, account verification, and saving and loading all five Skills. If anything is missing, state that installation is incomplete. If automatic loading in a new conversation has not been verified, mark it as "new conversation verification pending"; success in the current conversation is not verification across conversations.

If the user has already specified an Agent or a task, preserve the name, ID, and original request, and hand off to the appropriate Skill to continue. If there is no task, provide only a short usage example, such as "Use OpenAgent to help me find a travel planning Agent." Do not automatically execute paid tasks for installation acceptance.
